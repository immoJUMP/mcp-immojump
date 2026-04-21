from typing import Any

from .._shared import _call_with_client, _ok, destructive_op, read_only, write_op


def register(mcp):
    @mcp.tool(annotations=read_only())
    def pipeline_count(
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Return pipeline count for organisation."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.pipeline_count(),
        )
        return _ok(result)

    @mcp.tool(annotations=read_only())
    def pipeline_list(
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List all pipelines for organisation."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.pipeline_list(),
        )
        return _ok(result)

    @mcp.tool(annotations=read_only())
    def pipeline_get(
        pipeline_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Get a single pipeline by id."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.pipeline_get(pipeline_id=pipeline_id),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def pipeline_create(
        name,
        token=None,
        organisation_id=None,
        entity_type='immobilie',
        order=None,
        base_url=None,
    ):
        """Create a pipeline.

        - entity_type: immobilie, contact, or deal (default: immobilie)
        """

        payload: dict[str, Any] = {'name': name, 'entity_type': entity_type}
        if order is not None:
            payload['order'] = order

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.pipeline_create(data=payload),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def pipeline_update(
        pipeline_id,
        token=None,
        organisation_id=None,
        name=None,
        entity_type=None,
        order=None,
        regenerate_inbound_email_prefix=None,
        base_url=None,
    ):
        """Update an existing pipeline."""

        payload: dict[str, Any] = {}
        if name is not None:
            payload['name'] = name
        if entity_type is not None:
            payload['entity_type'] = entity_type
        if order is not None:
            payload['order'] = order
        if regenerate_inbound_email_prefix is not None:
            payload['regenerate_inbound_email_prefix'] = bool(regenerate_inbound_email_prefix)

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.pipeline_update(pipeline_id=pipeline_id, data=payload),
        )
        return _ok(result)

    @mcp.tool(annotations=destructive_op())
    def pipeline_delete(
        pipeline_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Delete a pipeline."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.pipeline_delete(pipeline_id=pipeline_id),
        )
        return _ok(result)

    @mcp.tool(annotations=read_only())
    def pipeline_export(
        pipeline_id,
        token=None,
        organisation_id=None,
        format='yaml',
        base_url=None,
    ):
        """Export pipeline definition as yaml or json."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.pipeline_export(pipeline_id=pipeline_id, format=format),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def pipeline_import(
        payload,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Import a pipeline definition from YAML string or JSON object."""

        if not isinstance(payload, (dict, str)):
            raise ValueError('payload must be an object or yaml string')

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.pipeline_import(payload=payload),
        )
        return _ok(result)

    @mcp.tool(annotations=read_only())
    def pipeline_statuses_list(
        pipeline_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List statuses for a pipeline."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.pipeline_statuses_list(pipeline_id=pipeline_id),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def pipeline_status_create(
        pipeline_id,
        name,
        token=None,
        organisation_id=None,
        entity_type=None,
        order=None,
        base_url=None,
    ):
        """Create a status in a pipeline."""

        payload: dict[str, Any] = {'name': name}
        if entity_type is not None:
            payload['entity_type'] = entity_type
        if order is not None:
            payload['order'] = order

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.pipeline_status_create(pipeline_id=pipeline_id, data=payload),
        )
        return _ok(result)

    @mcp.tool(annotations=destructive_op())
    def pipeline_status_delete(
        pipeline_id,
        status_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Delete a status through pipeline-scoped endpoint."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.pipeline_status_delete(pipeline_id=pipeline_id, status_id=status_id),
        )
        return _ok(result)
