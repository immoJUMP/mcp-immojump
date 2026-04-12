from .._app import mcp, _call_with_client, _ok, _require_dict


@mcp.tool()
def tickets_statuses(
    token,
    organisation_id,
    base_url=None,
):
    """List available ticket statuses (Kanban columns)."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.tickets_statuses(),
    )
    return _ok(result)


@mcp.tool()
def tickets_list(
    token,
    organisation_id,
    page=1,
    per_page=25,
    status=None,
    search=None,
    base_url=None,
):
    """List tickets (Kanban cards) with pagination and optional filters.

    - status: filter by ticket status
    - search: free-text query
    """

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.tickets_list(
            page=int(page),
            per_page=int(per_page),
            status=status,
            search=search,
        ),
    )
    return _ok(result)


@mcp.tool()
def tickets_get(
    ticket_id,
    token,
    organisation_id,
    base_url=None,
):
    """Get full details for a single ticket by UUID."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.tickets_get(ticket_id=ticket_id),
    )
    return _ok(result)


@mcp.tool()
def tickets_create(
    data,
    token,
    organisation_id,
    base_url=None,
):
    """Create a new ticket.

    Common fields: title, description, status, priority,
    assigned_to, immobilie_id, contact_id, due_date.
    """

    payload = _require_dict(field_name='data', value=data)
    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.tickets_create(data=payload),
    )
    return _ok(result)


@mcp.tool()
def tickets_update(
    ticket_id,
    data,
    token,
    organisation_id,
    base_url=None,
):
    """Update a ticket (full update)."""

    payload = _require_dict(field_name='data', value=data)
    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.tickets_update(ticket_id=ticket_id, data=payload),
    )
    return _ok(result)


@mcp.tool()
def tickets_delete(
    ticket_id,
    token,
    organisation_id,
    base_url=None,
):
    """Delete a ticket permanently."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.tickets_delete(ticket_id=ticket_id),
    )
    return _ok(result)


@mcp.tool()
def tickets_change_status(
    ticket_id,
    status,
    token,
    organisation_id,
    base_url=None,
):
    """Move a ticket to a different Kanban column (change status)."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.tickets_change_status(ticket_id=ticket_id, status=status),
    )
    return _ok(result)


@mcp.tool()
def tickets_list_comments(
    ticket_id,
    token,
    organisation_id,
    base_url=None,
):
    """List comments/activity on a ticket."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.tickets_list_comments(ticket_id=ticket_id),
    )
    return _ok(result)


@mcp.tool()
def tickets_add_comment(
    ticket_id,
    data,
    token,
    organisation_id,
    base_url=None,
):
    """Add a comment to a ticket.

    data: {"text": "Comment text"} or {"content": "..."}.
    """

    payload = _require_dict(field_name='data', value=data)
    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.tickets_add_comment(ticket_id=ticket_id, data=payload),
    )
    return _ok(result)
