from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import ImmojumpAPIClient, ImmojumpCredentials


def _resolve_mcp_host() -> str:
    return str(
        os.getenv('IMMOJUMP_MCP_HOST')
        or os.getenv('FASTMCP_HOST')
        or '127.0.0.1'
    ).strip()


def _resolve_mcp_port() -> int:
    raw = str(
        os.getenv('IMMOJUMP_MCP_PORT')
        or os.getenv('FASTMCP_PORT')
        or '8000'
    ).strip()
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'Invalid MCP port: {raw}') from exc


mcp = FastMCP(
    'immojump-contacts',
    host=_resolve_mcp_host(),
    port=_resolve_mcp_port(),
)


def _require_text(*, field_name: str, value: str | None) -> str:
    resolved = str(value or '').strip()
    if not resolved:
        raise ValueError(f'{field_name} is required')
    return resolved


def _require_dict(*, field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f'{field_name} must be an object')
    return value


def _require_list(*, field_name: str, value: Any) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f'{field_name} must be a list')
    return value


def _resolve_credentials(
    *,
    base_url: str | None,
    token: str | None,
    organisation_id: str | None,
) -> ImmojumpCredentials:
    return ImmojumpCredentials(
        base_url=base_url or os.getenv('IMMOJUMP_BASE_URL', ''),
        token=_require_text(field_name='token', value=token),
        organisation_id=_require_text(field_name='organisation_id', value=organisation_id),
    )


def _call_with_client(
    *,
    base_url: str | None,
    token: str | None,
    organisation_id: str | None,
    callback,
) -> Any:
    creds = _resolve_credentials(base_url=base_url, token=token, organisation_id=organisation_id)
    with ImmojumpAPIClient(creds) as client:
        return callback(client)


def _ok(result: Any) -> dict[str, Any]:
    return {'ok': True, 'result': result}


@mcp.tool()
def connection_test(
    token,
    organisation_id,
    base_url=None,
):
    """Validate API credentials and organisation access."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.connection_test(),
    )
    return _ok(result)


@mcp.tool()
def contacts_import_preview(
    source_type,
    token,
    organisation_id,
    source_text=None,
    file_path=None,
    sheet_name=None,
    mapping_overrides=None,
    smart=True,
    base_url=None,
):
    """Preview contact import using dry_run mode."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.contacts_import_unified(
            source_type=source_type,
            dry_run=True,
            smart=smart,
            source_text=source_text,
            file_path=file_path,
            sheet_name=sheet_name,
            mapping_overrides=mapping_overrides,
        ),
    )
    return _ok(result)


@mcp.tool()
def contacts_import_start(
    source_type,
    token,
    organisation_id,
    source_text=None,
    file_path=None,
    sheet_name=None,
    mapping_overrides=None,
    smart=True,
    base_url=None,
):
    """Start asynchronous contact import job."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.contacts_import_unified(
            source_type=source_type,
            dry_run=False,
            smart=smart,
            source_text=source_text,
            file_path=file_path,
            sheet_name=sheet_name,
            mapping_overrides=mapping_overrides,
        ),
    )
    return _ok(result)


@mcp.tool()
def contacts_job_status(
    job_id,
    token,
    organisation_id,
    base_url=None,
):
    """Read import job status."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.contacts_job_status(job_id=job_id),
    )
    return _ok(result)


@mcp.tool()
def contacts_job_resume(
    job_id,
    token,
    organisation_id,
    base_url=None,
):
    """Resume a failed/cancelled import job."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.contacts_job_resume(job_id=job_id),
    )
    return _ok(result)


@mcp.tool()
def contacts_job_cancel(
    job_id,
    token,
    organisation_id,
    base_url=None,
):
    """Request cancellation for an import job."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.contacts_job_cancel(job_id=job_id),
    )
    return _ok(result)


@mcp.tool()
def contacts_duplicates_preview(
    token,
    organisation_id,
    by='email,phone,mobile,name',
    min_count=2,
    limit_groups=200,
    ignore_generic_names=True,
    base_url=None,
):
    """Preview duplicate-contact groups."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.contacts_duplicates_preview(
            by=by,
            min_count=min_count,
            limit_groups=limit_groups,
            ignore_generic_names=ignore_generic_names,
        ),
    )
    return _ok(result)


@mcp.tool()
def contacts_merge_apply(
    primary_id,
    duplicate_ids,
    token,
    organisation_id,
    base_url=None,
):
    """Execute contact merge for confirmed duplicates."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.contacts_merge_apply(primary_id=primary_id, duplicate_ids=duplicate_ids),
    )
    return _ok(result)


@mcp.tool()
def pipeline_count(
    token,
    organisation_id,
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


@mcp.tool()
def pipeline_list(
    token,
    organisation_id,
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


@mcp.tool()
def pipeline_get(
    pipeline_id,
    token,
    organisation_id,
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


@mcp.tool()
def pipeline_create(
    name,
    token,
    organisation_id,
    entity_type='immobilie',
    description=None,
    icon=None,
    tags=None,
    order=None,
    base_url=None,
):
    """Create a pipeline."""

    payload: dict[str, Any] = {'name': name, 'entity_type': entity_type}
    if description is not None:
        payload['description'] = description
    if icon is not None:
        payload['icon'] = icon
    if tags is not None:
        payload['tags'] = tags
    if order is not None:
        payload['order'] = order

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.pipeline_create(data=payload),
    )
    return _ok(result)


@mcp.tool()
def pipeline_update(
    pipeline_id,
    token,
    organisation_id,
    name=None,
    entity_type=None,
    description=None,
    icon=None,
    tags=None,
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
    if description is not None:
        payload['description'] = description
    if icon is not None:
        payload['icon'] = icon
    if tags is not None:
        payload['tags'] = tags
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


@mcp.tool()
def pipeline_delete(
    pipeline_id,
    token,
    organisation_id,
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


@mcp.tool()
def pipeline_export(
    pipeline_id,
    token,
    organisation_id,
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


@mcp.tool()
def pipeline_import(
    payload,
    token,
    organisation_id,
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


@mcp.tool()
def pipeline_statuses_list(
    pipeline_id,
    token,
    organisation_id,
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


@mcp.tool()
def pipeline_status_create(
    pipeline_id,
    name,
    token,
    organisation_id,
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


@mcp.tool()
def pipeline_status_delete(
    pipeline_id,
    status_id,
    token,
    organisation_id,
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


@mcp.tool()
def status_list(
    token,
    organisation_id,
    base_url=None,
):
    """List all statuses for organisation."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.status_list(),
    )
    return _ok(result)


@mcp.tool()
def status_update(
    status_id,
    data,
    token,
    organisation_id,
    base_url=None,
):
    """Update status fields."""

    payload = _require_dict(field_name='data', value=data)
    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.status_update(status_id=status_id, data=payload),
    )
    return _ok(result)


@mcp.tool()
def status_delete(
    status_id,
    token,
    organisation_id,
    base_url=None,
):
    """Delete status by id."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.status_delete(status_id=status_id),
    )
    return _ok(result)


@mcp.tool()
def status_swap_order(
    current_status_id,
    target_status_id,
    current_status_order,
    target_status_order,
    token,
    organisation_id,
    base_url=None,
):
    """Swap order of two statuses in same pipeline."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.status_swap_order(
            current_status_id=current_status_id,
            target_status_id=target_status_id,
            current_status_order=current_status_order,
            target_status_order=target_status_order,
        ),
    )
    return _ok(result)


@mcp.tool()
def status_inbound_aliases_list(
    status_id,
    token,
    organisation_id,
    base_url=None,
):
    """List inbound email aliases for a status."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.status_inbound_aliases_list(status_id=status_id),
    )
    return _ok(result)


@mcp.tool()
def status_inbound_alias_create(
    status_id,
    token,
    organisation_id,
    prefix=None,
    base_url=None,
):
    """Create inbound alias for a status, optional explicit UUID prefix."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.status_inbound_alias_create(status_id=status_id, prefix=prefix),
    )
    return _ok(result)


@mcp.tool()
def activity_templates_list(
    token,
    organisation_id,
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
    token,
    organisation_id,
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
    token,
    organisation_id,
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
    token,
    organisation_id,
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
    token,
    organisation_id,
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
    token,
    organisation_id,
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
    token,
    organisation_id,
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
    token,
    organisation_id,
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


def main() -> None:
    transport = str(os.getenv('IMMOJUMP_MCP_TRANSPORT', 'sse')).strip().lower()
    if transport not in {'sse', 'streamable-http', 'stdio'}:
        raise ValueError('IMMOJUMP_MCP_TRANSPORT must be one of: sse, streamable-http, stdio')
    mcp.run(transport=transport)


if __name__ == '__main__':
    main()
