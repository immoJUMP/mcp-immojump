from .._shared import _call_with_client, _ok, read_only, write_op


def register(mcp):
    @mcp.tool(annotations=write_op())
    def valuation_request(
        immobilie_id,
        provider=None,
        force_refresh=False,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Request a market valuation (market value + market rent) for a property.

        Only the property id is needed: the server reads address, living space
        (sum of the units), property type and construction year from the property.

        - provider: one provider per call, 'geomap' (default) or 'fpre'.
          Call valuation_providers to see available options.
        - force_refresh: false (default) returns a recent cached valuation;
          true requests a new, billable valuation from the provider.

        Errors carry a German reason to pass on to the user plus a code, e.g.
        VALUATION_PROPERTY_TYPE_UNSUPPORTED (FPRE only values apartments,
        single- and multi-family houses) or VALUATION_INPUT_INCOMPLETE (address
        or living space missing — complete the property first).
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.valuation_request(
                immobilie_id=immobilie_id, provider=provider, force_refresh=force_refresh,
            ),
        )
        return _ok(result)

    @mcp.tool(annotations=read_only())
    def valuation_history(
        immobilie_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Get valuation history for a property (all past valuations)."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.valuation_history(immobilie_id=immobilie_id),
        )
        return _ok(result)

    @mcp.tool(annotations=read_only())
    def valuation_providers(
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List available valuation providers and their status."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.valuation_providers(),
        )
        return _ok(result)
