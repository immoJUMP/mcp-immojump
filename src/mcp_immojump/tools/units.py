from .._shared import _call_with_client, _ok, _require_dict


def register(mcp):
    @mcp.tool()
    def units_list(
        immobilie_id,
        token,
        organisation_id,
        base_url=None,
    ):
        """List all units (apartments) for a multi-family property."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.units_list(immobilie_id=immobilie_id),
        )
        return _ok(result)

    @mcp.tool()
    def units_count(
        token,
        organisation_id,
        base_url=None,
    ):
        """Return total unit count across all properties."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.units_count(),
        )
        return _ok(result)

    @mcp.tool()
    def units_create(
        immobilie_id,
        data,
        token,
        organisation_id,
        base_url=None,
    ):
        """Create a new unit for a multi-family property.

        Common fields: name, wohnflaeche, miete_kalt, miete_ist,
        zimmer, stockwerk, leerstand.
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.units_create(immobilie_id=immobilie_id, data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def units_update(
        unit_id,
        data,
        token,
        organisation_id,
        base_url=None,
    ):
        """Update an existing unit."""

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.units_update(unit_id=unit_id, data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def units_delete(
        unit_id,
        token,
        organisation_id,
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
