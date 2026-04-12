from .._shared import _call_with_client, _ok, _require_dict


def register(mcp):
    # ------------------------------------------------------------------
    # Search Profiles
    # ------------------------------------------------------------------

    @mcp.tool()
    def investor_search_profile_get(
        org_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Get the current user's investor search profile for an organisation."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_search_profile_get(org_id=org_id),
        )
        return _ok(result)

    @mcp.tool()
    def investor_search_profile_save(
        org_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Save/update the current user's investor search profile.

        data: search criteria fields (property types, locations, budget, etc.)
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_search_profile_save(org_id=org_id, data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def investor_search_profiles(
        org_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List all search profiles for the current user in an organisation."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_search_profiles(org_id=org_id),
        )
        return _ok(result)

    @mcp.tool()
    def investor_search_profile_submissions(
        org_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List all search profile submissions (admin view)."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_search_profile_submissions(org_id=org_id),
        )
        return _ok(result)

    @mcp.tool()
    def investor_search_profile_submission_update(
        org_id,
        submission_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Update a search profile submission (admin – approve/reject/edit)."""

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_search_profile_submission_update(
                org_id=org_id, submission_id=submission_id, data=payload,
            ),
        )
        return _ok(result)

    # ------------------------------------------------------------------
    # Search Profile Masks (admin)
    # ------------------------------------------------------------------

    @mcp.tool()
    def investor_search_profile_masks(
        org_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List search profile masks (form definitions for investor criteria)."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_search_profile_masks(org_id=org_id),
        )
        return _ok(result)

    @mcp.tool()
    def investor_search_profile_mask_create(
        org_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create a new search profile mask (admin)."""

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_search_profile_mask_create(org_id=org_id, data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def investor_search_profile_mask_update(
        org_id,
        mask_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Update a search profile mask (admin)."""

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_search_profile_mask_update(
                org_id=org_id, mask_id=mask_id, data=payload,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def investor_search_profile_mask_delete(
        org_id,
        mask_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Delete a search profile mask (admin)."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_search_profile_mask_delete(org_id=org_id, mask_id=mask_id),
        )
        return _ok(result)

    # ------------------------------------------------------------------
    # Investor Assignments
    # ------------------------------------------------------------------

    @mcp.tool()
    def investor_assignments_list(
        org_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List all investor assignments for an organisation (admin)."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_assignments_list(org_id=org_id),
        )
        return _ok(result)

    @mcp.tool()
    def investor_assignments_create(
        org_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create an investor assignment (assign property to investor).

        data: {"immobilie_id": "...", "user_id": "..."} (+ optional fields).
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_assignments_create(org_id=org_id, data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def investor_assignments_bulk(
        org_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Bulk-create investor assignments."""

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_assignments_bulk(org_id=org_id, data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def investor_assignment_update(
        org_id,
        assignment_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Update an investor assignment."""

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_assignment_update(
                org_id=org_id, assignment_id=assignment_id, data=payload,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def investor_assignment_delete(
        org_id,
        assignment_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Delete an investor assignment."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_assignment_delete(
                org_id=org_id, assignment_id=assignment_id,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def investor_my_assignments(
        org_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List property assignments for the current investor user."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_my_assignments(org_id=org_id),
        )
        return _ok(result)

    @mcp.tool()
    def investor_my_assignment_get(
        org_id,
        assignment_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Get details for a specific assignment (investor view)."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_my_assignment_get(
                org_id=org_id, assignment_id=assignment_id,
            ),
        )
        return _ok(result)

    # ------------------------------------------------------------------
    # Matching Config & Reporting
    # ------------------------------------------------------------------

    @mcp.tool()
    def investor_matching_config(
        org_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Get the matching configuration (how investors are matched to properties)."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_matching_config(org_id=org_id),
        )
        return _ok(result)

    @mcp.tool()
    def investor_matching_config_update(
        org_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Update the matching configuration."""

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_matching_config_update(org_id=org_id, data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def investor_reporting(
        org_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Get investor portal reporting/analytics data."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_reporting(org_id=org_id),
        )
        return _ok(result)

    @mcp.tool()
    def investor_my_assignment_favorite(
        org_id,
        assignment_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Toggle favorite status for an assignment (investor view)."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_my_assignment_favorite(
                org_id=org_id, assignment_id=assignment_id,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def investor_my_assignment_accept_agreement(
        org_id,
        assignment_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Accept the legal agreement for a property assignment."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_my_assignment_accept_agreement(
                org_id=org_id, assignment_id=assignment_id,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def investor_finance_defaults(
        org_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Get default finance parameters for investor calculations."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_finance_defaults(org_id=org_id),
        )
        return _ok(result)

    @mcp.tool()
    def investor_finance_defaults_update(
        org_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Update default finance parameters for investor calculations."""

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_finance_defaults_update(org_id=org_id, data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def investor_matching_config_reset(
        org_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Reset matching configuration to defaults."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_matching_config_reset(org_id=org_id),
        )
        return _ok(result)

    @mcp.tool()
    def investor_inquiry(
        org_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Submit an investor inquiry for a property.

        data: {"assignment_id": "...", "message": "..."}.
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_inquiry(org_id=org_id, data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def investor_legal_docs(
        org_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Get legal documents for the investor portal."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.investor_legal_docs(org_id=org_id),
        )
        return _ok(result)
