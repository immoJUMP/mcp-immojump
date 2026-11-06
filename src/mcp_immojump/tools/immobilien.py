from .._shared import (
    _as_bool,
    _call_with_client,
    _id_list,
    _ok,
    _require_dict,
    _require_list,
    _require_text,
    destructive_op,
    read_only,
    write_op,
)


def register(mcp):
    @mcp.tool(annotations=read_only())
    def property_intelligence_get(immobilie_id, token=None, organisation_id=None, base_url=None):
        """Load the investor overview: chosen profile, missing documents, opportunities, risks and
        preferences."""
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.property_intelligence_get(immobilie_id=immobilie_id),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def property_intelligence_settings(
        immobilie_id, data, token=None, organisation_id=None, base_url=None
    ):
        """Update the personal settings of the investor overview. data takes only these keys:
        - profile_id: UUID of one of your own search profiles in this organisation, or null
        - phase: "initial" (first check) or "purchase" (purchase decision)
        - checklist: {category: status}, e.g. {"grundbuch": "requested"}; only the
          given categories change. Status: missing, requested, present, incomplete,
          reviewed, not_relevant
        - extra_categories: list of further document categories to track
        - target_yield: gross target yield in percent, 1 to 15, or null for the default
        Categories: expose, mieterliste, mietvertrag, energieausweis, grundbuch,
        grundriss, wohnflaechenberechnung, betriebskosten, teilungserklaerung,
        wirtschaftsplan, hausgeldabrechnung, weg_protokoll, baulasten, altlasten,
        bauunterlagen, versicherung, kaufvertrag, rechnung, finanzierung, sonstiges.
        Any other key or value is rejected with a generic 400; business rules stay
        in the backend."""
        payload = _require_dict(field_name="data", value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.property_intelligence_settings(
                immobilie_id=immobilie_id, data=payload
            ),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def property_intelligence_decide(
        immobilie_id, data, token=None, organisation_id=None, base_url=None
    ):
        """Record an explicit customer decision. data: outcome pursue/hold/reject, reason
        renovation/location/price/yield/other, request_id (a new UUID; resending the
        same one is idempotent) and optional note (text, at most 2000 characters).
        Never infer consent."""
        payload = _require_dict(field_name="data", value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.property_intelligence_decide(
                immobilie_id=immobilie_id, data=payload
            ),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def property_intelligence_analyze(
        immobilie_id, token=None, organisation_id=None, base_url=None
    ):
        """Request a deeper source-grounded assessment. Consumes an AI analysis allowance; may take
        45 seconds."""
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.property_intelligence_analyze(immobilie_id=immobilie_id),
        )
        return _ok(result)

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

        # Local import keeps the module's import line untouched (parallel PRs).
        from .._shared import _id_list

        status_list = _id_list(field_name='status_ids', value=status_ids) if status_ids else None
        tag_list = _id_list(field_name='tag_ids', value=tag_ids) if tag_ids else None

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.immobilien_search(
                search=search,
                status_ids=status_list,
                tag_ids=tag_list,
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

        data fields (all optional; other top-level keys are ignored):
        - name: display name, defaults to daten.adresse
        - type: property type code, one of ETW, EFH, MFH, WGH, GEW, Sonstiges
          (default ETW). German labels such as "Mehrfamilienhaus" are accepted;
          anything else is rejected with HTTP 400 and valid_values.
        - daten: the property data, e.g. {"adresse": "Roermonder Str. 15,
          52072 Aachen", "kaufpreis": 380000, "baujahr": 1965}
        - status_id: pipeline status to place the property in
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
        Does not move the property in the pipeline: status_id at the top level of
        data is rejected with 400 (code STATUS_VIA_PUT) and nothing is changed; a
        text status, or a status_id inside a nested "daten" block, is dropped with a
        warning while the other fields are saved. Use immobilien_update_status for
        the pipeline status.

        Only include the fields you want to modify, e.g.
        {"kaufpreis": 350000, "wohnflaeche": 85}
        type takes the property type code ETW, EFH, MFH, WGH, GEW or Sonstiges
        (German labels such as "Gewerbe" are accepted).
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

    @mcp.tool(annotations=read_only())
    def immobilien_merge_preview(
        immobilie_ids,
        primary_id=None,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Step 1 of merging duplicate properties: show what a merge would do. Changes nothing.

        Always call this before immobilien_merge and show the conflicts to the user.

        - immobilie_ids: list of 2 to 10 property IDs of the same organisation
        - primary_id: the property to keep (must be in immobilie_ids); default is
          the oldest one, because it usually carries the history

        Returns primary_id, properties (name, address, attached counts),
        can_merge (false = you lack update on the primary or delete on a duplicate),
        conflicts (fields where several properties hold different values; each
        with field, label, default and the candidate values per immobilie_id),
        filled (empty fields of the primary that get filled automatically) and
        blocks (einheiten, kalkulation, finanzierung — only listed when more than
        one property has data; each block comes as a whole from ONE property).
        Unknown or foreign IDs return 404.
        """

        ids = _id_list(field_name='immobilie_ids', value=immobilie_ids)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.immobilien_merge_preview(
                immobilie_ids=ids,
                primary_id=primary_id,
            ),
        )
        return _ok(result)

    @mcp.tool(annotations=destructive_op())
    def immobilien_merge(
        primary_id,
        duplicate_ids,
        field_choices=None,
        block_choices=None,
        include_documents=True,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Step 2: merge duplicate properties into one. Call immobilien_merge_preview first.

        - primary_id: the property that stays
        - duplicate_ids: list of 1 to 9 property IDs merged into it
        - field_choices: {field: immobilie_id} answering the preview's conflicts,
          e.g. {"name": "<id>", "asking_price": "<id>"}. Fields: name, type,
          status_id, adresse, baujahr, grundstueck, asking_price,
          acquisition_price, sale_price, target_sale_price
        - block_choices: {block: immobilie_id}, blocks: einheiten (units and rent
          roll), kalkulation (calculation and costs), finanzierung (loans). A
          block is taken as a whole from the chosen property, never mixed.
        - include_documents: move documents and images to the primary (default
          true); false leaves them on the duplicates
        Unanswered conflicts take the preview's default. Everything else
        (activities, tags, milestones, shares, valuations, ...) moves to the
        primary, notes are appended.

        The duplicates go to the trash (soft delete), they are not destroyed.
        The response carries log_id; immobilien_merge_restore with it undoes the
        merge. Needs update on the primary and delete on every duplicate (403).
        """

        dup_ids = _id_list(field_name='duplicate_ids', value=duplicate_ids)
        fields_ = _require_dict(field_name='field_choices', value=field_choices) if field_choices else {}
        blocks = _require_dict(field_name='block_choices', value=block_choices) if block_choices else {}
        documents = _as_bool(field_name='include_documents', value=include_documents)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.immobilien_merge(
                primary_id=_require_text(field_name='primary_id', value=primary_id),
                duplicate_ids=dup_ids,
                field_choices=fields_,
                block_choices=blocks,
                include_documents=documents,
            ),
        )
        return _ok(result)

    @mcp.tool(annotations=read_only())
    def immobilien_merge_logs(
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List the last 50 property merges of the organisation.

        Each entry: id (the log_id for immobilien_merge_restore), created_at,
        primary and duplicates (id + name), restored_at and restorable (false
        once undone or when a duplicate was taken out of the trash meanwhile).
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.immobilien_merge_logs(),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def immobilien_merge_restore(
        log_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Undo a property merge: the duplicates come back from the trash and
        moved data returns to them.

        - log_id: the "id" of an entry from immobilien_merge_logs, or the log_id
          returned by immobilien_merge

        Values changed on the primary after the merge stay as they are; the
        response lists them in kept_fields. A merge can be undone once (409
        afterwards). Needs update on the primary and unrestricted delete rights.
        """

        log = _require_text(field_name='log_id', value=log_id)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.immobilien_merge_restore(log_id=log),
        )
        return _ok(result)
