from .._shared import _call_with_client, _ok, _require_dict


def register(mcp):
    @mcp.tool()
    def milestones_list(
        immobilie_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List all milestones/deadlines for a property.

        Returns milestones with type, date, status (PLANNED/DONE/MISSED),
        title, description, reminders, and links.

        Milestone types: NOTAR_BEURKUNDUNG, KAUFPREIS_FAELLIG,
        KAUFPREIS_ZAHLUNG, BNL, HANDOVER, PRIORITY_NOTICE, OWNERSHIP_REG,
        FINANCE_COMMITMENT, LOAN_DISBURSEMENT, INTEREST_FIX_END,
        BK_ABRECHNUNG_FAELLIG, WARTUNG, ENERGIEAUSWEIS_ENDE,
        GEWAEHRLEISTUNG_ENDE, VERKAUF_BEURKUNDUNG, VERKAUF_BNL, OTHER.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.milestones_list(immobilie_id=immobilie_id),
        )
        return _ok(result)

    @mcp.tool()
    def milestones_create(
        immobilie_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create a milestone/deadline for a property.

        Required in data:
        - type: milestone type (see milestones_list for enum values)
        - date: ISO date or datetime string, e.g. "2026-06-15"

        Optional:
        - title: custom title (auto-generated from type if omitted)
        - description: notes
        - all_day: true (default) or false for time-specific milestones
        - status: PLANNED (default), DONE, or MISSED
        - completed_at: ISO datetime (for DONE status)
        - reminder_days_before: list of ints, e.g. [7, 14] for reminders
        - links_json: list of {"url": "...", "title": "..."} objects

        Note: Setting a milestone auto-syncs the corresponding date field
        on the property (e.g. BNL milestone updates immobilie.bnl_date).
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.milestones_create(
                immobilie_id=immobilie_id, data=payload,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def milestones_update(
        milestone_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Update a milestone (partial update – only provided fields change).

        All fields from milestones_create are updatable.
        Changing the type also updates which property date field is synced.
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.milestones_update(
                milestone_id=milestone_id, data=payload,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def milestones_delete(
        milestone_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Delete a milestone. Clears the synced date field on the property."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.milestones_delete(milestone_id=milestone_id),
        )
        return _ok(result)
