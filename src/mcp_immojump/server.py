"""immoJUMP MCP server – monolithic entry point.

For production use, prefer the domain-specific servers in ``servers/``
(properties, crm, pipeline, org) which each expose 36-58 tools.

This monolithic server is kept for backward compatibility and development.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ._shared import (  # noqa: F401  — re-exported for test backward compat
    _resolve_mcp_host,
    _resolve_mcp_port,
    _resolve_credentials,
    _call_with_client,
    _ok,
    _require_text,
    _require_dict,
    _require_list,
)
from .tools import (
    connection,
    immobilien,
    contacts,
    activities,
    activity_templates,
    custom_fields,
    deals,
    tickets,
    documents,
    loans,
    milestones,
    units,
    tags,
    organisation,
    feed,
    email_messages,
    valuation,
    user,
    pipelines,
    statuses,
)

mcp = FastMCP(
    'immojump',
    host=_resolve_mcp_host(),
    port=_resolve_mcp_port(),
)

# Register ALL domains on the monolithic instance.
connection.register(mcp)
immobilien.register(mcp)
contacts.register(mcp)
activities.register(mcp)
activity_templates.register(mcp)
custom_fields.register(mcp)
deals.register(mcp)
tickets.register(mcp)
documents.register(mcp)
loans.register(mcp)
milestones.register(mcp)
units.register(mcp)
tags.register(mcp)
organisation.register(mcp)
feed.register(mcp)
email_messages.register(mcp)
valuation.register(mcp)
user.register(mcp)
pipelines.register(mcp)
statuses.register(mcp)


def main() -> None:
    from .servers._base import run_server
    run_server(mcp)


if __name__ == '__main__':
    main()
