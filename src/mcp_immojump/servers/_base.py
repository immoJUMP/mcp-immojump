"""Shared factory for creating domain MCP servers with auth + OAuth support."""

from __future__ import annotations

import os

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import ASGIApp, Receive, Scope, Send

from .._shared import _resolve_mcp_host, _resolve_mcp_port, ctx_token, ctx_organisation_id
from ..oauth import create_oauth_routes, decode_access_token


class _AuthMiddleware:
    """Extract credentials from HTTP headers into contextvars.

    Supports three auth methods (in order):
    1. Direct headers: Authorization: Bearer <api_token> + X-Organisation-Id: <org>
    2. OAuth access token: Authorization: Bearer <base64(api_token:org_id)>
    3. No auth: tools will ask for credentials as parameters

    For unauthenticated MCP requests, returns 401 with WWW-Authenticate
    pointing to the OAuth discovery endpoint (required by MCP spec).
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

    # Build combined ASGI app: OAuth routes + MCP server
    if transport == 'sse':
        mcp_app = mcp.sse_app()
    else:
        mcp_app = mcp.streamable_http_app()

    # Wrap MCP with auth middleware
    authed_mcp = _AuthMiddleware(mcp_app)

    # Create combined Starlette app with OAuth + MCP
    oauth_routes = create_oauth_routes()

    # OAuth routes are served directly, MCP routes are mounted at the transport path
    # We need a catch-all that falls through: OAuth routes first, then MCP
    app = Starlette(
        routes=[
            *oauth_routes,
            # Mount MCP as catch-all for /mcp, /sse, and other paths
            Mount('/', app=authed_mcp),
        ],
    )

    uvicorn.run(
        app,
        host=_resolve_mcp_host(),
        port=_resolve_mcp_port(),
    )
