"""Shared factory for creating domain MCP servers."""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from .._shared import _resolve_mcp_host, _resolve_mcp_port


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
    mcp.run(transport=transport)
