"""immoJUMP Organisation MCP server.

Domains: Organisation, Feed, Email, Custom Fields, User.
~58 tools.
"""

from ._base import create_server, run_server
from ..tools import connection, organisation, feed, email_messages, custom_fields, user

mcp = create_server('immojump-org')

connection.register(mcp)
organisation.register(mcp)
feed.register(mcp)
email_messages.register(mcp)
custom_fields.register(mcp)
user.register(mcp)


def main() -> None:
    run_server(mcp)


if __name__ == '__main__':
    main()
