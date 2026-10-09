from .._shared import _call_with_client, _ok, _require_dict, read_only, write_op


def register(mcp):
    @mcp.tool(annotations=read_only())
    def deals_list(
        token=None,
        organisation_id=None,
        pipeline_id=None,
        status_id=None,
        search=None,
        base_url=None,
    ):
        """List all deals of the organisation, optionally filtered.

        Not paginated: returns every matching deal as a list. Narrow the
        result with the filters instead (they combine with AND).

        - pipeline_id: integer ID of a pipeline (use pipeline_list)
        - status_id: integer ID of a pipeline status (use pipeline_statuses_list)
        - search: free text, matched case-insensitively against deal name and
          description

        A non-integer pipeline_id/status_id is rejected with HTTP 400.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.deals_list(
                pipeline_id=pipeline_id,
                status_id=status_id,
                search=search,
            ),
        )
        return _ok(result)

    @mcp.tool(annotations=read_only())
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

    @mcp.tool(annotations=write_op())
    def deals_create(
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create a new deal.

        data: JSON object with:

        Required:
        - name: string (title of the deal)

        Optional:
        - status_id: integer ID of a status in a deal pipeline (pipeline_list →
          pipeline with entity_type "deal", then pipeline_statuses_list).
          There is no pipeline_id field — the pipeline follows from status_id.
        - immobilie_ids: list of property IDs. A property can sit in only one
          deal; linking one that is already taken fails with a message naming
          the other deal.
        - contact_ids: list of contact UUIDs
        - assignee_ids: list of integer user IDs
        - tag_ids: list of tag IDs
        - description: string
        - deal_amount: number (deal value)
        - currency: string, default "EUR"
        - probability: integer percentage (0–100)
        - next_step: string
        - expected_close_date: ISO datetime or date-only string, e.g. "2026-06-01"
          (auto-expanded to midnight UTC)

        Legacy names title/value/notes and singular immobilie_id/contact_id are
        mapped to name/deal_amount/description/immobilie_ids/contact_ids; giving
        both with different values is rejected. pipeline_id is rejected.
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.deals_create(data=payload),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def deals_update(
        deal_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Update an existing deal (partial update via PATCH — only provided fields change).

        deal_id: UUID of the deal.
        data: any of the deals_create fields (none required). Set status_id to
        move the deal to another stage. List fields (immobilie_ids, contact_ids,
        assignee_ids, tag_ids) REPLACE the current links — send the full list;
        an empty list removes all links. expected_close_date accepts date-only
        strings. regenerate_inbound_email_prefix: true issues a new inbound
        e-mail address for the deal.
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.deals_update(deal_id=deal_id, data=payload),
        )
        return _ok(result)
