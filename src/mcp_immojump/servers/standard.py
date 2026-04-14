"""Standard MCP server — 88 tools for everyday investor workflows.

Covers: Immobilien, Units, Kontakte, Aktivitäten, Activity Templates,
Pipelines, Statuses, Tags, Dokumente.
"""
from ._base import create_server, run_server
from ..tools import (
    connection, immobilien, units, contacts, activities,
    activity_templates, pipelines, statuses, tags, documents,
)

mcp = create_server('immojump-standard')

connection.register(mcp)
immobilien.register(mcp)
units.register(mcp)
contacts.register(mcp)
activities.register(mcp)
activity_templates.register(mcp)
pipelines.register(mcp)
statuses.register(mcp)
tags.register(mcp)
documents.register(mcp)


def main() -> None:
    run_server(mcp)
