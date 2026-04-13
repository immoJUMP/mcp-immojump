"""Shared factory for creating domain MCP servers with auth + OAuth support."""

from __future__ import annotations

import os

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from .._shared import _resolve_mcp_host, _resolve_mcp_port, ctx_token, ctx_organisation_id
from ..oauth import create_oauth_routes, decode_access_token


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
    _MCP_PATHS = ('/mcp', '/sse')

    def __init__(self, mcp_app: ASGIApp):
        self.mcp_app = mcp_app
        self.oauth_app = Starlette(routes=create_oauth_routes())

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] == 'http':
            path = scope.get('path', '')

            # OAuth routes → OAuth app
            if any(path.startswith(p) for p in self._OAUTH_PREFIXES):
                await self.oauth_app(scope, receive, send)
                return

            # MCP routes without auth → 401 with WWW-Authenticate
            if any(path.startswith(p) for p in self._MCP_PATHS):
                headers = dict(scope.get('headers', []))
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

    def __init__(self, mcp: FastMCP):
        self.sse_app = _AuthMiddleware(mcp.sse_app())
        self.http_app = _AuthMiddleware(mcp.streamable_http_app())

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get('path', '')
        if path.startswith('/sse'):
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
