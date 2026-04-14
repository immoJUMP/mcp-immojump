"""Profi MCP server — 130 tools for professional investors.

Standard + Deals, Tickets, Milestones, Custom Fields, Email-Inbox.
"""
from ._base import create_server, run_server
from ..tools import (
    connection, immobilien, units, contacts, activities,
    activity_templates, pipelines, statuses, tags, documents,
    deals, tickets, milestones, custom_fields, email_messages,
)

mcp = create_server('immojump-profi')

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
deals.register(mcp)
tickets.register(mcp)
milestones.register(mcp)
custom_fields.register(mcp)
email_messages.register(mcp)


def main() -> None:
    run_server(mcp)
