from .._shared import _call_with_client, _ok, _require_dict


def register(mcp):
    @mcp.tool()
    def activities_list(
        token,
        organisation_id,
        page=1,
        per_page=25,
        search=None,
        status=None,
        type=None,
        base_url=None,
    ):
        """List activities/tasks with pagination and optional filters.

        - search: free-text query
        - status: filter by activity status (e.g. open, done)
        - type: filter by activity type (e.g. call, email, meeting, task)
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activities_list(
                page=int(page),
                per_page=int(per_page),
                search=search,
                status=status,
                type=type,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def activities_get(
        activity_id,
        token,
        organisation_id,
        base_url=None,
    ):
        """Get full details for a single activity by ID."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activities_get(activity_id=activity_id),
        )
        return _ok(result)

    @mcp.tool()
    def activities_create(
        data,
        token,
        organisation_id,
        base_url=None,
    ):
        """Create a new activity/task.

        Common fields: title, description, type (call/email/meeting/task),
        due_date, assigned_to, priority, status.
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activities_create(data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def activities_create_for_property(
        immobilie_id,
        data,
        token,
        organisation_id,
        base_url=None,
    ):
        """Create an activity linked to a specific property."""

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activities_create_for_property(
                immobilie_id=immobilie_id, data=payload,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def activities_update(
        activity_id,
        data,
        token,
        organisation_id,
        base_url=None,
    ):
        """Update an existing activity."""

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activities_update(activity_id=activity_id, data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def activities_delete(
        activity_id,
        token,
        organisation_id,
        base_url=None,
    ):
        """Delete an activity permanently."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activities_delete(activity_id=activity_id),
        )
        return _ok(result)

    @mcp.tool()
    def activities_list_by_property(
        immobilie_id,
        token,
        organisation_id,
        base_url=None,
    ):
        """List all activities linked to a specific property."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activities_list_by_property(immobilie_id=immobilie_id),
        )
        return _ok(result)

    @mcp.tool()
    def activities_statistics(
        token,
        organisation_id,
        base_url=None,
    ):
        """Get activity statistics for the organisation (counts by status/type)."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activities_statistics(),
        )
        return _ok(result)

    @mcp.tool()
    def activities_structure_description(
        text,
        token,
        organisation_id,
        base_url=None,
    ):
        """Use AI to structure a free-text activity description into a proper format."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activities_structure_description(text=text),
        )
        return _ok(result)

    @mcp.tool()
    def activities_calendar_generate_link(
        token,
        organisation_id,
        base_url=None,
    ):
        """Generate an iCalendar (.ics) sharing link for activities.

        Returns a URL that can be subscribed to in any calendar app.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activities_calendar_generate_link(),
        )
        return _ok(result)
