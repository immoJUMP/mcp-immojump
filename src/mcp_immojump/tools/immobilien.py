from .._shared import _call_with_client, _ok, _require_dict, _require_list, destructive_op, read_only, write_op


def register(mcp):
    @mcp.tool(annotations=read_only())
    def immobilien_list(
        token=None,
        organisation_id=None,
        page=1,
        per_page=25,
        base_url=None,
    ):
        """List properties for the organisation with pagination.

        Returns a paginated list of Immobilie objects.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.immobilien_list(page=int(page), per_page=int(per_page)),
        )
        return _ok(result)

    @mcp.tool(annotations=read_only())
    def immobilien_search(
        token=None,
        organisation_id=None,
        search=None,
        status_ids=None,
        tag_ids=None,
        page=1,
        per_page=25,
        base_url=None,
    ):
        """Search properties by text, status IDs, and/or tag IDs.

        - search: free-text query (address, title, etc.)
        - status_ids: list of pipeline status IDs to filter by
        - tag_ids: list of tag IDs to filter by
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.immobilien_search(
                search=search,
                status_ids=status_ids,
                tag_ids=tag_ids,
                page=int(page),
                per_page=int(per_page),
            ),
        )
        return _ok(result)

    @mcp.tool(annotations=read_only())
    def immobilien_count(
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Return the total number of properties for the organisation."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.immobilien_count(),
        )
        return _ok(result)

    @mcp.tool(annotations=read_only())
    def immobilien_get(
        immobilie_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Get full details for a single property by ID.

        Returns all fields: address, financials, status, tags, units, etc.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.immobilien_get(immobilie_id=immobilie_id),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def immobilien_create(
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create a new property.

        data must include at minimum: title or address fields.
        Common fields: title, strasse, hausnummer, plz, ort, kaufpreis,
        wohnflaeche, grundstuecksflaeche, baujahr, zimmer.
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.immobilien_create(data=payload),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def immobilien_update_status(
        immobilie_id,
        status_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Move a property to another pipeline status, or take it out of the pipeline.

        status_id: integer ID of the target status (use pipeline_statuses_list
        to find valid status IDs for a pipeline); null removes the property
        from its pipeline. Changes nothing but the status -- property fields
        go through immobilien_patch.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.immobilien_update_status(
                immobilie_id=immobilie_id,
                status_id=status_id,
            ),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def immobilien_patch(
        immobilie_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Partial update of a property (PATCH -- only provided fields change).
        Does not move the property in the pipeline: a status_id sent here only
        lands in the property data. Use immobilien_update_status for that.

        Only include the fields you want to modify, e.g.
        {"kaufpreis": 350000, "wohnflaeche": 85}
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.immobilien_patch(immobilie_id=immobilie_id, data=payload),
        )
        return _ok(result)

    @mcp.tool(annotations=destructive_op())
    def immobilien_delete(
        immobilie_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Delete a property permanently."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.immobilien_delete(immobilie_id=immobilie_id),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def immobilien_duplicate(
        immobilie_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create a copy of an existing property.

        Returns the new property with a fresh ID.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.immobilien_duplicate(immobilie_id=immobilie_id),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def immobilien_transfer(
        immobilie_id,
        target_organisation_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Transfer a property to another organisation."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.immobilien_transfer(
                immobilie_id=immobilie_id,
                target_organisation_id=target_organisation_id,
            ),
        )
        return _ok(result)

    @mcp.tool(annotations=read_only())
    def immobilien_contacts(
        immobilie_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List contacts linked to a property (sellers, buyers, agents, etc.)."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.immobilien_contacts(immobilie_id=immobilie_id),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def immobilien_split_units(
        immobilie_id,
        unit_ids,
        target_type=None,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Split units of a multi-family property (type MFH) into separate properties.

        - unit_ids: list of unit IDs to split off (units_list shows them); each
          becomes its own property with a copy of the data, tags and status
        - target_type: property type of the new properties, one of ETW, EFH,
          MFH, WGH, GEW, Sonstiges (default ETW)

        The original MFH stays unchanged. Returns the created properties.
        """

        ids = _require_list(field_name='unit_ids', value=unit_ids)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.immobilien_split_units(
                immobilie_id=immobilie_id,
                unit_ids=ids,
                target_type=target_type,
            ),
        )
        return _ok(result)
