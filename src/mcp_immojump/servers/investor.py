"""immoJUMP Investor Portal MCP server.

Domains: Investor Portal (search profiles, masks, assignments, matching, reporting).
~26 tools.
"""

from ._base import create_server, run_server
from ..tools import connection, investor

mcp = create_server('immojump-investor')

connection.register(mcp)
investor.register(mcp)


def main() -> None:
    run_server(mcp)


if __name__ == '__main__':
    main()
