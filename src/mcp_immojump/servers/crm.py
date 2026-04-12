"""immoJUMP CRM MCP server.

Domains: Contacts, Activities, Tags.
~36 tools.
"""

from ._base import create_server, run_server
from ..tools import connection, contacts, activities, tags

mcp = create_server('immojump-crm')

connection.register(mcp)
contacts.register(mcp)
activities.register(mcp)
tags.register(mcp)


def main() -> None:
    run_server(mcp)


if __name__ == '__main__':
    main()
