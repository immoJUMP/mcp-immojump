from .._shared import _call_with_client, _ok, _require_dict, _require_list, destructive_op, read_only, write_op


def register(mcp):
    @mcp.tool(annotations=read_only())
    def activity_templates_list(
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List activity templates for organisation."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activity_templates_list(),
        )
        return _ok(result)

    @mcp.tool(annotations=read_only())
    def activity_templates_recurring_list(
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List recurring activity templates for organisation."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activity_templates_recurring_list(),
        )
        return _ok(result)

    @mcp.tool(annotations=read_only())
    def activity_templates_by_status(
        status_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List activity templates bound to a pipeline status.

        status_id: integer ID of a pipeline status (not an activity status string).
        Use pipeline_statuses_list to find valid status IDs.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activity_templates_by_status(status_id=status_id),
        )
        return _ok(result)

    @mcp.tool(annotations=read_only())
    def activity_template_get(
        template_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Get activity template by id."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activity_template_get(template_id=template_id),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def activity_template_create(
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create an activity template.

        data: JSON object with:

        Required:
        - title: string
        - activity_status: Geplant, In Bearbeitung, Abgeschlossen, or Abgebrochen
        - type: ANRUF, BESICHTIGUNG, BRIEF, E-MAIL, MEETING, NOTIZ, or SONSTIGES
        - priority: Hoch, Mittel, Niedrig, or NA
        - mode: task, decision, or recurring
          (recurring requires recurrence_rule, e.g. "FREQ=WEEKLY;INTERVAL=1")

        Optional:
        - description: string (plain text or HTML)
        - status_id: integer ID of a pipeline status — binds this template
          to a pipeline phase (auto-created when entity enters that status)
        - assignee_mode: who gets the created task (default "fixed"):
          - "fixed": the user in assigned_to_id (optionally with assigned_role_id)
          - "role": only assigned_role_id (assigned_to_id is dropped)
          - "actor": whoever moved the entity into the status. assigned_to_id /
            assigned_role_id are the fallback when no human changed the status
            (API access token ijr_/ijw_, n8n, bots, ImmoMetrica import) or the
            person left the organisation; without them the task stays unassigned.
        - assigned_to_id: integer user ID to auto-assign (fallback in mode "actor")
        - assigned_role_id: UUID of a role to auto-assign
        - start_in_days: integer — auto-set start date N days after creation
        - end_in_days: integer — auto-set due date N days after creation
        - decision_question: string (required when mode=decision)
        - outcomes: list of {key, label, actions}; actions:
          - {"type": "STATUS_CHANGE", "target_status_id": <int>}
          - {"type": "CREATE_ACTIVITY", "template_id": "<uuid>"} or
            {"type": "CREATE_ACTIVITY", "title": "..."} (inline task)
        - next_activity_template_id: UUID of the follow-up template (chain)

        target_status_id, template_id and next_activity_template_id must belong
        to the SAME organisation as the template: take status IDs from
        pipeline_statuses_list and template IDs from earlier create responses.
        IDs of other organisations are rejected exactly like unknown IDs
        (HTTP 400, message ends with "nicht gefunden.").
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activity_template_create(data=payload),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def activity_template_update(
        template_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Update activity template with safe outcome semantics.

        Payload controls in `data`:
        - `replace_outcomes` (bool, optional): default false, merge by outcome.id.
        - `if_updated_at` (string, optional): optimistic concurrency guard (409 on mismatch).
        - `dry_run` (bool, optional): return diff preview without persisting.

        Fields as in activity_template_create, e.g. {"assignee_mode": "actor"}
        to give the task to whoever changes the status (assigned_to_id /
        assigned_role_id stay as fallback).

        Same reference rule as activity_template_create: target_status_id,
        template_id and next_activity_template_id must belong to the template's
        organisation (HTTP 400 "... nicht gefunden." otherwise). Moving a
        template into another organisation's status is rejected while its
        saved outcomes still point into the old organisation.
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activity_template_update(template_id=template_id, data=payload),
        )
        return _ok(result)

    @mcp.tool(annotations=destructive_op())
    def activity_template_delete(
        template_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Delete activity template."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activity_template_delete(template_id=template_id),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def activity_templates_batch_move(
        template_ids,
        target_status_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Move multiple activity templates to a new status."""

        ids = _require_list(field_name='template_ids', value=template_ids)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activity_templates_batch_move(
                template_ids=ids,
                target_status_id=target_status_id,
            ),
        )
        return _ok(result)
