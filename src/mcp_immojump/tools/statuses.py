from .._app import mcp, _call_with_client, _ok, _require_dict


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
