"""immoJUMP Pipeline MCP server.

Domains: Pipelines, Statuses, Activity Templates, Deals, Tickets.
~39 tools.
"""

from ._base import create_server, run_server
from ..tools import connection, pipelines, statuses, activity_templates, deals, tickets

mcp = create_server('immojump-pipeline')

connection.register(mcp)
pipelines.register(mcp)
statuses.register(mcp)
activity_templates.register(mcp)
deals.register(mcp)
tickets.register(mcp)


def main() -> None:
    run_server(mcp)


if __name__ == '__main__':
    main()
