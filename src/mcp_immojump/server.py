"""ImmoJUMP MCP server – entry point.

Tool registrations live in ``tools/`` sub-modules; they are imported here so
that all tools are discovered when the server starts.  Shared helpers are in
``_app.py`` and re-exported below for backward compatibility with existing
tests.
"""

from __future__ import annotations

import os

# Re-export shared state & helpers so ``import mcp_immojump.server as server``
# followed by ``server._resolve_credentials(...)`` keeps working in tests.
from ._app import (  # noqa: F401
    mcp,
    _resolve_mcp_host,
    _resolve_mcp_port,
    _resolve_credentials,
    _call_with_client,
    _ok,
    _require_text,
    _require_dict,
    _require_list,
)

# Importing the tools package triggers all ``@mcp.tool()`` registrations.
from . import tools as _tools  # noqa: F401


def main() -> None:
    transport = str(os.getenv('IMMOJUMP_MCP_TRANSPORT', 'sse')).strip().lower()
    if transport not in {'sse', 'streamable-http', 'stdio'}:
        raise ValueError('IMMOJUMP_MCP_TRANSPORT must be one of: sse, streamable-http, stdio')
    mcp.run(transport=transport)


if __name__ == '__main__':
    main()
