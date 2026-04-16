from .._shared import _call_with_client, _ok, _require_dict


def register(mcp):
    @mcp.tool()
    def activities_meta(
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Get valid enum values for activity filters.

        Returns: statuses, types, priorities — use these values when
        filtering activities_list. Call this first if unsure which
        filter values are allowed.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activities_meta(),
        )
        return _ok(result)

    @mcp.tool()
    def activities_list(
        token=None,
        organisation_id=None,
        page=1,
        per_page=25,
        search=None,
        status=None,
        type=None,
        base_url=None,
    ):
        """List activities/tasks with pagination and optional filters.

        - search: free-text query
        - status: one of Geplant, In Bearbeitung, Abgeschlossen, Abgebrochen
        - type: one of ANRUF, BESICHTIGUNG, BRIEF, E-MAIL, MEETING, NOTIZ, SONSTIGES

        Call activities_meta first to get all valid filter values.
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
        token=None,
        organisation_id=None,
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
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create a new activity/task.

        data: JSON object with:

        Required:
        - title: string
        - type: ANRUF, BESICHTIGUNG, BRIEF, E-MAIL, MEETING, NOTIZ, or SONSTIGES
        - activity_status: Geplant, In Bearbeitung, Abgeschlossen, or Abgebrochen
        - priority: Hoch, Mittel, Niedrig, or NA

        Optional:
        - description: string (plain text or HTML)
        - due_date: ISO datetime or date-only string, e.g. "2026-04-23T09:00:00Z"
          or "2026-04-23" (auto-expanded to midnight UTC)
        - assigned_to_id: UUID of the user to assign
        - immobilien_id: integer ID of the linked property
        - contact_ids: list of contact UUID strings, e.g. ["uuid-1", "uuid-2"]

        Call activities_meta first if unsure about valid enum values.
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
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create an activity linked to a specific property.

        immobilie_id: integer ID of the property.
        data: same fields as activities_create (title, type, activity_status, priority required).
        The activity is automatically linked to the property.
        """

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
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Update an existing activity.

        activity_id: UUID of the activity.
        data: JSON object with fields to update (partial — only provided fields change).
        Same fields as activities_create. due_date accepts date-only strings.
        """

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
        token=None,
        organisation_id=None,
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
        token=None,
        organisation_id=None,
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
        token=None,
        organisation_id=None,
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
        token=None,
        organisation_id=None,
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
        token=None,
        organisation_id=None,
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
