"""immoJUMP Properties MCP server.

Domains: Immobilien, Units, Loans, Milestones, Documents, Valuation.
~39 tools.
"""

from ._base import create_server, run_server
from ..tools import connection, immobilien, units, loans, milestones, documents, valuation

mcp = create_server('immojump-properties')

connection.register(mcp)
immobilien.register(mcp)
units.register(mcp)
loans.register(mcp)
milestones.register(mcp)
documents.register(mcp)
valuation.register(mcp)


def main() -> None:
    run_server(mcp)


if __name__ == '__main__':
    main()
