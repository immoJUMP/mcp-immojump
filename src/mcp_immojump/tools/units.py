from .._shared import _call_with_client, _ok, _require_dict, destructive_op, read_only, write_op


def register(mcp):
    @mcp.tool(annotations=read_only())
    def units_list(
        immobilie_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List the units (apartments, shops, parking spaces) of a property.

        Every property created via immobilien_create starts with one empty
        default unit "Einheit 1" (0 m2, rent 0). Fill it with units_update or,
        once another unit exists, remove it with units_delete. Left empty, it
        stays in the rent roll, and immobilien_split_units turns it into its
        own property with purchase price 0 -- pass only real units there.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.units_list(immobilie_id=immobilie_id),
        )
        return _ok(result)

    @mcp.tool(annotations=read_only())
    def units_count(
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Count the units created by the calling user.

        Counts across all properties and organisations; organisation_id has
        no effect. For the units of one property use units_list.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.units_count(),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def units_create(
        immobilie_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create a new unit (apartment, shop, parking space) for a property.

        A new property already has an empty default unit "Einheit 1" (see
        units_list): put the first unit there with units_update instead of
        creating a second one next to it.

        data fields (all optional). Any other key is rejected with HTTP 400:
        valid_fields lists the accepted names, field_suggestions names the
        right field for a near miss. An unknown type returns valid_values.
        Numbers are JSON numbers with a decimal point (62.5, not "62,5");
        an unreadable number or date is rejected with HTTP 400 and the field
        named in errors, nothing is written.
        - einheit: unit name, e.g. "WE 1" or "EG links"
        - livingspace: area in m2; immobilien_split_units splits the purchase
          price in proportion to it. Keep 0 for garage and stellplatz.
        - rooms: number of rooms, e.g. 2.5
        - type: wohnen, gewerbe, stellplatz, garage or sonstiges (default wohnen)
        - ist_rent: current monthly cold rent (Kaltmiete) in EUR (default 0)
        - soll_rent: first target-rent scenario per month (defaults to ist_rent)
        - soll_rent2: second target-rent scenario per month (defaults to soll_rent)
        - note: free text, e.g. tenant name or vacancy
        - order: sort position in the rent roll, a whole number; leave it out to
          append the unit at the end, after "Einheit 1"
        - lease_start_date, last_rent_increase_date: YYYY-MM-DD or DD.MM.YYYY
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.units_create(immobilie_id=immobilie_id, data=payload),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def units_update(
        unit_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Update an existing unit.

        Only include the fields you want to change, e.g.
        {"ist_rent": 720, "note": "Mieterhöhung 2026"}. Any other key is
        rejected with HTTP 400 (valid_fields, field_suggestions); an unknown
        type returns valid_values. Numbers are JSON numbers with a decimal
        point (62.5, not "62,5"); an unreadable number or date returns 400
        and changes nothing. Fields of the unit response (id,
        immobilie_id, source, ...) may be sent back unchanged and are not
        written. Fields:
        - einheit: unit name
        - livingspace: area in m2; immobilien_split_units splits the purchase
          price in proportion to it. Keep 0 for garage and stellplatz.
        - rooms: number of rooms
        - type: wohnen, gewerbe, stellplatz, garage or sonstiges
        - ist_rent: current monthly cold rent (Kaltmiete) in EUR
        - soll_rent, soll_rent2: target-rent scenarios per month (not
          adjusted when ist_rent changes)
        - note: free text
        - order: sort position in the rent roll
        - lease_start_date, last_rent_increase_date: YYYY-MM-DD or
          DD.MM.YYYY; null clears the date
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.units_update(unit_id=unit_id, data=payload),
        )
        return _ok(result)

    @mcp.tool(annotations=destructive_op())
    def units_delete(
        unit_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Delete a unit permanently."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.units_delete(unit_id=unit_id),
        )
        return _ok(result)
