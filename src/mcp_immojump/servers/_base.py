"""Shared factory for creating domain MCP servers with auth + OAuth support."""

from __future__ import annotations

import os
from urllib.parse import urlparse

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from .._shared import _resolve_mcp_host, _resolve_mcp_port, ctx_token, ctx_organisation_id
from ..oauth import create_oauth_routes, decode_access_token


# ---------------------------------------------------------------------------
# Origin header validation (DNS-rebind protection)
# ---------------------------------------------------------------------------
# Default allowlist covers the official MCP clients that consume this server
# (Claude.ai, ChatGPT). Operators can extend via the
# IMMOJUMP_MCP_ALLOWED_ORIGINS env var (comma-separated full origins, e.g.
# "https://claude.ai,https://example.com").
#
# Non-browser clients (Claude Desktop, Codex CLI) omit Origin entirely; we
# treat an empty Origin as "not a browser" and let it through — the bearer
# token is the authentication boundary in that case.

_DEFAULT_ALLOWED_ORIGINS: frozenset[str] = frozenset({
    'https://claude.ai',
    'https://claude.com',
    'https://chat.openai.com',
    'https://chatgpt.com',
})

_LOOPBACK_HOSTS: frozenset[str] = frozenset({'localhost', '127.0.0.1', '::1'})


def _allowed_origins() -> frozenset[str]:
    extra = os.getenv('IMMOJUMP_MCP_ALLOWED_ORIGINS', '').strip()
    if not extra:
        return _DEFAULT_ALLOWED_ORIGINS
    parsed = {origin.strip().rstrip('/') for origin in extra.split(',') if origin.strip()}
    return _DEFAULT_ALLOWED_ORIGINS | frozenset(parsed)


def _is_origin_allowed(origin: str) -> bool:
    """Return True if the Origin header matches an allowed scheme+host(+port).

    An Origin per RFC 6454 is ``scheme://host[:port]`` with no path.  We
    reject anything containing a path component so that loose matches like
    ``http://localhost/evil`` cannot slip through the loopback fallback.
    Loopback hosts are accepted on both http and https so local dev servers
    behind mkcert/Caddy also work.
    """
    if not origin:
        return False
    origin = origin.strip()
    if origin in _allowed_origins():
        return True
    try:
        parsed = urlparse(origin)
    except ValueError:
        return False
    if parsed.scheme not in {'http', 'https'}:
        return False
    if parsed.path not in ('', '/'):
        return False
    if parsed.query or parsed.fragment:
        return False
    host = (parsed.hostname or '').lower()
    return host in _LOOPBACK_HOSTS


class _AuthMiddleware:
    """Extract credentials from HTTP headers into contextvars.

    Supports three auth methods (in order):
    1. Direct headers: Authorization: Bearer <api_token> + X-Organisation-Id: <org>
    2. OAuth access token: Authorization: Bearer <base64(api_token:org_id)>
    3. No auth: tools will ask for credentials as parameters
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] in ('http', 'websocket'):
            headers = dict(scope.get('headers', []))
            auth = headers.get(b'authorization', b'').decode()
            org_id = headers.get(b'x-organisation-id', b'').decode().strip()

            if auth.lower().startswith('bearer '):
                bearer_value = auth[7:].strip()

                if org_id:
                    # Method 1: Direct headers (Claude Code, Cursor, etc.)
                    ctx_token.set(bearer_value)
                    ctx_organisation_id.set(org_id)
                else:
                    # Method 2: Try decoding as OAuth access_token (ChatGPT)
                    decoded = decode_access_token(bearer_value)
                    if decoded:
                        ctx_token.set(decoded[0])
                        ctx_organisation_id.set(decoded[1])
                    else:
                        # Plain Bearer token without org — tools will ask
                        ctx_token.set(bearer_value)

        await self.app(scope, receive, send)


class _OAuthFrontMiddleware:
    """Route OAuth paths to the OAuth app, everything else to the MCP app.

    Also returns 401 + WWW-Authenticate for unauthenticated MCP requests
    so OAuth clients (ChatGPT) can discover the auth server.
    """

    _OAUTH_PREFIXES = ('/.well-known/oauth-', '/oauth/')
    _MCP_PATHS = ('/mcp', '/sse', '/messages')

    def __init__(self, mcp_app: ASGIApp):
        self.mcp_app = mcp_app
        self.oauth_app = Starlette(routes=create_oauth_routes())

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] == 'http':
            path = scope.get('path', '')
            headers_raw = scope.get('headers', [])

            # Origin validation on MCP routes (DNS-rebind / CSRF protection).
            # Browsers send Origin on cross-origin requests; non-browser clients
            # (Claude Desktop, Codex CLI) omit it, which is also allowed.
            if any(path.startswith(p) for p in self._MCP_PATHS):
                origin = next(
                    (v.decode().strip() for k, v in headers_raw if k == b'origin'),
                    '',
                )
                if origin and not _is_origin_allowed(origin):
                    resp = Response(
                        content='Origin not allowed',
                        status_code=403,
                    )
                    await resp(scope, receive, send)
                    return

            # OAuth routes → OAuth app
            if any(path.startswith(p) for p in self._OAUTH_PREFIXES):
                await self.oauth_app(scope, receive, send)
                return

            # MCP routes without auth → 401 with WWW-Authenticate
            if any(path.startswith(p) for p in self._MCP_PATHS):
                headers = dict(headers_raw)
                auth = headers.get(b'authorization', b'').decode().strip()
                if not auth:
                    server_url = os.getenv('IMMOJUMP_MCP_PUBLIC_URL', '').strip()
                    if not server_url:
                        host = next(
                            (v.decode() for k, v in scope.get('headers', []) if k == b'host'),
                            'mcp.immojump.de',
                        )
                        scheme = next(
                            (v.decode() for k, v in scope.get('headers', []) if k == b'x-forwarded-proto'),
                            'https',
                        )
                        server_url = f'{scheme}://{host}'
                    metadata_url = f'{server_url}/.well-known/oauth-protected-resource'
                    resp = Response(
                        content='Unauthorized',
                        status_code=401,
                        headers={
                            'WWW-Authenticate': f'Bearer resource_metadata="{metadata_url}", scope="immojump"',
                        },
                    )
                    await resp(scope, receive, send)
                    return

        await self.mcp_app(scope, receive, send)


def create_server(name: str) -> FastMCP:
    return FastMCP(
        name,
        host=_resolve_mcp_host(),
        port=_resolve_mcp_port(),
    )


class _DualTransportApp:
    """Serve both SSE (/sse) and Streamable HTTP (/mcp) on the same server.

    Claude Desktop uses /sse, ChatGPT uses /mcp (streamable-http).
    This middleware routes based on path prefix.
    """

    # SSE transport uses GET /sse for event stream + POST /messages for requests
    _SSE_PATHS = ('/sse', '/messages')

    def __init__(self, mcp: FastMCP):
        self.sse_app = _AuthMiddleware(mcp.sse_app())
        self.http_app = _AuthMiddleware(mcp.streamable_http_app())

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get('path', '')
        if any(path.startswith(p) for p in self._SSE_PATHS):
            await self.sse_app(scope, receive, send)
        else:
            await self.http_app(scope, receive, send)


def run_server(mcp: FastMCP) -> None:
    transport = str(os.getenv('IMMOJUMP_MCP_TRANSPORT', 'sse')).strip().lower()
    if transport not in {'sse', 'streamable-http', 'stdio'}:
        raise ValueError('IMMOJUMP_MCP_TRANSPORT must be one of: sse, streamable-http, stdio')

    if transport == 'stdio':
        mcp.run(transport='stdio')
        return

    # Serve both transports: /sse for Claude, /mcp for ChatGPT
    dual_mcp = _DualTransportApp(mcp)

    # Stack: OAuth front → dual transport MCP
    app = _OAuthFrontMiddleware(dual_mcp)

    uvicorn.run(
        app,
        host=_resolve_mcp_host(),
        port=_resolve_mcp_port(),
    )
