from .._app import mcp, _call_with_client, _ok, _require_dict


@mcp.tool()
def user_me(
    token,
    organisation_id,
    base_url=None,
):
    """Get current user profile (name, email, settings, organisations)."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.user_me(),
    )
    return _ok(result)


@mcp.tool()
def user_update_profile(
    data,
    token,
    organisation_id,
    base_url=None,
):
    """Update the current user's profile.

    Common fields: first_name, last_name, phone, company, position.
    """

    payload = _require_dict(field_name='data', value=data)
    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.user_update_profile(data=payload),
    )
    return _ok(result)
