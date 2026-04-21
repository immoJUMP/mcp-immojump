from .._shared import _call_with_client, _ok, _require_dict, destructive_op, read_only, write_op


def register(mcp):
    @mcp.tool(title='List ticket statuses', annotations=read_only())
    def tickets_statuses(
        token=None,
        organisation_id=None,
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

    @mcp.tool(title='List tickets', annotations=read_only())
    def tickets_list(
        token=None,
        organisation_id=None,
        page=1,
        per_page=25,
        status=None,
        search=None,
        base_url=None,
    ):
        """List tickets (Kanban cards) with pagination and optional filters.

        - status: ticket status name string (use tickets_statuses to get valid values)
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

    @mcp.tool(title='Get ticket', annotations=read_only())
    def tickets_get(
        ticket_id,
        token=None,
        organisation_id=None,
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

    @mcp.tool(title='Create ticket', annotations=write_op())
    def tickets_create(
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create a new ticket.

        data: JSON object with:

        Required:
        - title: string

        Optional:
        - description: string (plain text or HTML)
        - status: UUID string of a ticket status column
          (use tickets_statuses to list available statuses)
        - priority: low, medium, high, or urgent
        - assigned_to: UUID of the user to assign
        - immobilie_id: integer ID of the linked property
        - contact_id: UUID of the linked contact
        - due_date: ISO datetime or date-only string, e.g. "2026-05-15"
          (auto-expanded to midnight UTC)
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.tickets_create(data=payload),
        )
        return _ok(result)

    @mcp.tool(title='Update ticket', annotations=write_op())
    def tickets_update(
        ticket_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Update a ticket (full replace — include all fields you want to keep).

        ticket_id: UUID of the ticket.
        data: same fields as tickets_create. due_date accepts date-only strings.
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.tickets_update(ticket_id=ticket_id, data=payload),
        )
        return _ok(result)

    @mcp.tool(title='Delete ticket', annotations=destructive_op())
    def tickets_delete(
        ticket_id,
        token=None,
        organisation_id=None,
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

    @mcp.tool(title='Change ticket status', annotations=write_op())
    def tickets_change_status(
        ticket_id,
        status_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Move a ticket to a different Kanban column.

        status_id: UUID of the target ticket status.
        Use tickets_statuses to list available statuses.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.tickets_change_status(ticket_id=ticket_id, status_id=status_id),
        )
        return _ok(result)

    @mcp.tool(title='List ticket comments', annotations=read_only())
    def tickets_list_comments(
        ticket_id,
        token=None,
        organisation_id=None,
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

    @mcp.tool(title='Add ticket comment', annotations=write_op())
    def tickets_add_comment(
        ticket_id,
        data,
        token=None,
        organisation_id=None,
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
