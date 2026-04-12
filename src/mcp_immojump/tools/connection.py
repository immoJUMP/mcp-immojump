from .._app import mcp, _call_with_client, _ok


@mcp.tool()
def connection_test(
    token,
    organisation_id,
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
