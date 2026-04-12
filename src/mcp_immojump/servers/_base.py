"""Shared factory for creating domain MCP servers with header-based auth."""

from __future__ import annotations

import os

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.types import ASGIApp, Receive, Scope, Send

from .._shared import _resolve_mcp_host, _resolve_mcp_port, ctx_token, ctx_organisation_id


class _HeaderAuthMiddleware:
    """Extract Authorization + X-Organisation-Id from HTTP headers into contextvars.

    This lets tools resolve credentials automatically when headers are set
    in the Claude Code .mcp.json config, without requiring them as tool params.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] in ('http', 'websocket'):
            headers = dict(scope.get('headers', []))
            auth = headers.get(b'authorization', b'').decode()
            if auth.lower().startswith('bearer '):
                ctx_token.set(auth[7:].strip())
            org_id = headers.get(b'x-organisation-id', b'').decode().strip()
            if org_id:
                ctx_organisation_id.set(org_id)
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

    # For HTTP transports, wrap with header-auth middleware
    if transport == 'sse':
        app = mcp.sse_app()
    else:
        app = mcp.streamable_http_app()

    app = _HeaderAuthMiddleware(app)

    uvicorn.run(
        app,
        host=_resolve_mcp_host(),
        port=_resolve_mcp_port(),
    )
