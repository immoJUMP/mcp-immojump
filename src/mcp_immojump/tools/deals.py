from .._shared import _call_with_client, _ok, _require_dict


def register(mcp):
    @mcp.tool()
    def deals_list(
        token=None,
        organisation_id=None,
        page=1,
        per_page=25,
        pipeline_id=None,
        status_id=None,
        search=None,
        base_url=None,
    ):
        """List deals with pagination and optional filters.

        - pipeline_id: integer ID of a pipeline (use pipeline_list)
        - status_id: integer ID of a pipeline status (use pipeline_statuses_list)
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
        token=None,
        organisation_id=None,
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
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create a new deal.

        data: JSON object with:

        Required:
        - pipeline_id: integer ID of the pipeline (use pipeline_list)
        - status_id: integer ID of a status within that pipeline
          (use pipeline_statuses_list to get statuses for a pipeline)
        - immobilie_id: integer ID of the linked property

        Optional:
        - contact_id: UUID of the linked contact
        - title: string
        - value: number (deal value in EUR)
        - notes: string
        - expected_close_date: ISO datetime or date-only string, e.g. "2026-06-01"
          (auto-expanded to midnight UTC)
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
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Update an existing deal (partial update via PATCH — only provided fields change).

        deal_id: UUID of the deal.
        data: same fields as deals_create. Change status_id to move the deal
        to a different pipeline stage. expected_close_date accepts date-only strings.
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.deals_update(deal_id=deal_id, data=payload),
        )
        return _ok(result)
