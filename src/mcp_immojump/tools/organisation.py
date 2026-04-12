from .._shared import _call_with_client, _ok, _require_dict, _require_list


def register(mcp):
    @mcp.tool()
    def organisation_list(
        token,
        organisation_id,
        base_url=None,
    ):
        """List all organisations the current user belongs to."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.organisation_list(),
        )
        return _ok(result)

    @mcp.tool()
    def organisation_get(
        org_id,
        token,
        organisation_id,
        base_url=None,
    ):
        """Get full details for an organisation."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.organisation_get(org_id=org_id),
        )
        return _ok(result)

    @mcp.tool()
    def organisation_update(
        org_id,
        data,
        token,
        organisation_id,
        base_url=None,
    ):
        """Update organisation settings (name, logo, config)."""

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.organisation_update(org_id=org_id, data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def organisation_members(
        org_id,
        token,
        organisation_id,
        base_url=None,
    ):
        """List all members of an organisation with their roles."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.organisation_members(org_id=org_id),
        )
        return _ok(result)

    @mcp.tool()
    def organisation_update_member(
        org_id,
        user_id,
        data,
        token,
        organisation_id,
        base_url=None,
    ):
        """Update a member's settings in the organisation."""

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.organisation_update_member(
                org_id=org_id, user_id=user_id, data=payload,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def organisation_update_member_roles(
        org_id,
        user_id,
        role_ids,
        token,
        organisation_id,
        base_url=None,
    ):
        """Set roles for a member. role_ids replaces all current roles."""

        ids = _require_list(field_name='role_ids', value=role_ids)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.organisation_update_member_roles(
                org_id=org_id, user_id=user_id, role_ids=ids,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def organisation_remove_member(
        org_id,
        user_id,
        token,
        organisation_id,
        base_url=None,
    ):
        """Remove a member from the organisation."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.organisation_remove_member(org_id=org_id, user_id=user_id),
        )
        return _ok(result)

    @mcp.tool()
    def organisation_invites(
        org_id,
        token,
        organisation_id,
        base_url=None,
    ):
        """List pending invitations for an organisation."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.organisation_invites(org_id=org_id),
        )
        return _ok(result)

    @mcp.tool()
    def organisation_invite(
        org_id,
        data,
        token,
        organisation_id,
        base_url=None,
    ):
        """Invite a new member to the organisation.

        data: {"email": "...", "role": "..."}
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.organisation_invite(org_id=org_id, data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def organisation_cancel_invite(
        org_id,
        invite_id,
        token,
        organisation_id,
        base_url=None,
    ):
        """Cancel a pending invitation."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.organisation_cancel_invite(org_id=org_id, invite_id=invite_id),
        )
        return _ok(result)

    @mcp.tool()
    def organisation_roles(
        org_id,
        token,
        organisation_id,
        base_url=None,
    ):
        """List all roles defined for an organisation."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.organisation_roles(org_id=org_id),
        )
        return _ok(result)

    @mcp.tool()
    def organisation_create_role(
        org_id,
        data,
        token,
        organisation_id,
        base_url=None,
    ):
        """Create a custom role.

        data: {"name": "...", "permissions": [...]}
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.organisation_create_role(org_id=org_id, data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def organisation_update_role(
        org_id,
        role_id,
        data,
        token,
        organisation_id,
        base_url=None,
    ):
        """Update a custom role."""

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.organisation_update_role(
                org_id=org_id, role_id=role_id, data=payload,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def organisation_delete_role(
        org_id,
        role_id,
        token,
        organisation_id,
        base_url=None,
    ):
        """Delete a custom role."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.organisation_delete_role(org_id=org_id, role_id=role_id),
        )
        return _ok(result)

    @mcp.tool()
    def organisation_report_design(
        org_id,
        token,
        organisation_id,
        base_url=None,
    ):
        """Get the current report design/branding for an organisation."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.organisation_report_design(org_id=org_id),
        )
        return _ok(result)

    @mcp.tool()
    def organisation_rebuild_report_design(
        org_id,
        token,
        organisation_id,
        base_url=None,
    ):
        """Rebuild/regenerate the report design for an organisation."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.organisation_rebuild_report_design(org_id=org_id),
        )
        return _ok(result)
