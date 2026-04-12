from .._shared import _call_with_client, _ok


def register(mcp):
    @mcp.tool()
    def connection_test(
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Validate API credentials and organisation access.

        Returns the contact count for the organisation if successful.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.connection_test(),
        )
        return _ok(result)
