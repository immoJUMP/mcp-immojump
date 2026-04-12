"""Shared factory for creating domain MCP servers with auth + OAuth support."""

from __future__ import annotations

import os

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
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

    This avoids wrapping the MCP app in a new Starlette app (which breaks
    the MCP lifespan/task-group initialization).
    """

    _OAUTH_PREFIXES = ('/.well-known/oauth-', '/oauth/')

    def __init__(self, mcp_app: ASGIApp):
        self.mcp_app = mcp_app
        self.oauth_app = Starlette(routes=create_oauth_routes())

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] == 'http':
            path = scope.get('path', '')
            if any(path.startswith(p) for p in self._OAUTH_PREFIXES):
                await self.oauth_app(scope, receive, send)
                return
        await self.mcp_app(scope, receive, send)


def create_server(name: str) -> FastMCP:
    return FastMCP(
        name,
        host=_resolve_mcp_host(),
        port=_resolve_mcp_port(),
    )


def run_server(mcp: FastMCP) -> None:
    transport = str(os.getenv('IMMOJUMP_MCP_TRANSPORT', 'sse')).strip().lower()
    if transport not in {'sse', 'streamable-http', 'stdio'}:
        raise ValueError('IMMOJUMP_MCP_TRANSPORT must be one of: sse, streamable-http, stdio')

    if transport == 'stdio':
        mcp.run(transport='stdio')
        return

    # Build MCP app with auth middleware
    if transport == 'sse':
        mcp_app = mcp.sse_app()
    else:
        mcp_app = mcp.streamable_http_app()

    # Stack: OAuth front → Auth middleware → MCP app
    app = _OAuthFrontMiddleware(_AuthMiddleware(mcp_app))

    uvicorn.run(
        app,
        host=_resolve_mcp_host(),
        port=_resolve_mcp_port(),
    )
