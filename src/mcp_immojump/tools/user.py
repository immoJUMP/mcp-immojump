from .._shared import _call_with_client, _ok, _require_dict, read_only, write_op


def register(mcp):
    @mcp.tool(title='Get current user profile', annotations=read_only())
    def user_me(
        token=None,
        organisation_id=None,
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

    @mcp.tool(title='Update user profile', annotations=write_op())
    def user_update_profile(
        data,
        token=None,
        organisation_id=None,
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
