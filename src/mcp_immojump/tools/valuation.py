from .._shared import _call_with_client, _ok, read_only, write_op


def register(mcp):
    @mcp.tool(title='Request property valuation', annotations=write_op())
    def valuation_request(
        immobilie_id,
        token=None,
        organisation_id=None,
        providers=None,
        base_url=None,
    ):
        """Request a property valuation from external providers.

        - providers: optional list of provider names to use.
          Call valuation_providers to see available options.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.valuation_request(
                immobilie_id=immobilie_id, providers=providers,
            ),
        )
        return _ok(result)

    @mcp.tool(title='Get property valuation history', annotations=read_only())
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

    @mcp.tool(title='List valuation providers', annotations=read_only())
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
