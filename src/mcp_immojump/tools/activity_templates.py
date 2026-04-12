from .._shared import _call_with_client, _ok, _require_dict, _require_list


def register(mcp):
    @mcp.tool()
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

    @mcp.tool()
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

    @mcp.tool()
    def activity_templates_by_status(
        status_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List activity templates bound to a status."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activity_templates_by_status(status_id=status_id),
        )
        return _ok(result)

    @mcp.tool()
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

    @mcp.tool()
    def activity_template_create(
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create activity template."""

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activity_template_create(data=payload),
        )
        return _ok(result)

    @mcp.tool()
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
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.activity_template_update(template_id=template_id, data=payload),
        )
        return _ok(result)

    @mcp.tool()
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

    @mcp.tool()
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
