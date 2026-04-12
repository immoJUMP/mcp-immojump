from .._shared import _call_with_client, _ok, _require_dict


def register(mcp):
    @mcp.tool()
    def deals_list(
        token,
        organisation_id,
        page=1,
        per_page=25,
        pipeline_id=None,
        status_id=None,
        search=None,
        base_url=None,
    ):
        """List deals with pagination and optional filters.

        - pipeline_id: filter by pipeline
        - status_id: filter by pipeline status
        - search: free-text query
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.deals_list(
                page=int(page),
                per_page=int(per_page),
                pipeline_id=pipeline_id,
                status_id=status_id,
                search=search,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def deals_get(
        deal_id,
        token,
        organisation_id,
        base_url=None,
    ):
        """Get full details for a single deal by UUID."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.deals_get(deal_id=deal_id),
        )
        return _ok(result)

    @mcp.tool()
    def deals_create(
        data,
        token,
        organisation_id,
        base_url=None,
    ):
        """Create a new deal.

        Required: pipeline_id, status_id, immobilie_id.
        Optional: contact_id, title, value, notes.
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.deals_create(data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def deals_update(
        deal_id,
        data,
        token,
        organisation_id,
        base_url=None,
    ):
        """Update an existing deal (partial update via PATCH).

        Change status_id to move the deal to a different pipeline stage.
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.deals_update(deal_id=deal_id, data=payload),
        )
        return _ok(result)
