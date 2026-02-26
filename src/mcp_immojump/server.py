from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import ImmojumpAPIClient, ImmojumpCredentials


mcp = FastMCP('immojump-contacts')


def _resolve_credentials(
    *,
    base_url: str | None,
    token: str | None,
    organisation_id: str | None,
) -> ImmojumpCredentials:
    return ImmojumpCredentials(
        base_url=base_url or os.getenv('IMMOJUMP_BASE_URL', ''),
        token=token or os.getenv('IMMOJUMP_TOKEN', ''),
        organisation_id=organisation_id or os.getenv('IMMOJUMP_ORGANISATION_ID', ''),
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


@mcp.tool()
def connection_test(
    base_url=None,
    token=None,
    organisation_id=None,
):
    """Validate API credentials and organisation access."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.connection_test(),
    )
    return {
        'ok': True,
        'result': result,
    }


@mcp.tool()
def contacts_import_preview(
    source_type,
    source_text=None,
    file_path=None,
    sheet_name=None,
    mapping_overrides=None,
    smart=True,
    base_url=None,
    token=None,
    organisation_id=None,
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
    return {'ok': True, 'result': result}


@mcp.tool()
def contacts_import_start(
    source_type,
    source_text=None,
    file_path=None,
    sheet_name=None,
    mapping_overrides=None,
    smart=True,
    base_url=None,
    token=None,
    organisation_id=None,
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
    return {'ok': True, 'result': result}


@mcp.tool()
def contacts_job_status(
    job_id,
    base_url=None,
    token=None,
    organisation_id=None,
):
    """Read import job status."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.contacts_job_status(job_id=job_id),
    )
    return {'ok': True, 'result': result}


@mcp.tool()
def contacts_job_resume(
    job_id,
    base_url=None,
    token=None,
    organisation_id=None,
):
    """Resume a failed/cancelled import job."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.contacts_job_resume(job_id=job_id),
    )
    return {'ok': True, 'result': result}


@mcp.tool()
def contacts_job_cancel(
    job_id,
    base_url=None,
    token=None,
    organisation_id=None,
):
    """Request cancellation for an import job."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.contacts_job_cancel(job_id=job_id),
    )
    return {'ok': True, 'result': result}


@mcp.tool()
def contacts_duplicates_preview(
    by='email,phone,mobile,name',
    min_count=2,
    limit_groups=200,
    ignore_generic_names=True,
    base_url=None,
    token=None,
    organisation_id=None,
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
    return {'ok': True, 'result': result}


@mcp.tool()
def contacts_merge_apply(
    primary_id,
    duplicate_ids,
    base_url=None,
    token=None,
    organisation_id=None,
):
    """Execute contact merge for confirmed duplicates."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.contacts_merge_apply(primary_id=primary_id, duplicate_ids=duplicate_ids),
    )
    return {'ok': True, 'result': result}


def main() -> None:
    transport = str(os.getenv('IMMOJUMP_MCP_TRANSPORT', 'sse')).strip().lower()
    if transport not in {'sse', 'streamable-http', 'stdio'}:
        raise ValueError('IMMOJUMP_MCP_TRANSPORT must be one of: sse, streamable-http, stdio')
    mcp.run(transport=transport)


if __name__ == '__main__':
    main()
