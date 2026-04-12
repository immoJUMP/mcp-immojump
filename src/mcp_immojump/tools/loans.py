from .._app import mcp, _call_with_client, _ok, _require_dict, _require_list


@mcp.tool()
def loans_list(
    token,
    organisation_id,
    base_url=None,
):
    """List all loans for the organisation."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.loans_list(),
    )
    return _ok(result)


@mcp.tool()
def loans_create(
    data,
    token,
    organisation_id,
    base_url=None,
):
    """Create a new loan.

    Common fields: immobilie_id, bank_name, loan_amount, interest_rate,
    repayment_rate, term_years, start_date, type (annuity/bullet/etc).
    """

    payload = _require_dict(field_name='data', value=data)
    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.loans_create(data=payload),
    )
    return _ok(result)


@mcp.tool()
def loans_update(
    loan_id,
    data,
    token,
    organisation_id,
    base_url=None,
):
    """Update an existing loan."""

    payload = _require_dict(field_name='data', value=data)
    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.loans_update(loan_id=loan_id, data=payload),
    )
    return _ok(result)


@mcp.tool()
def loans_delete(
    loan_id,
    token,
    organisation_id,
    base_url=None,
):
    """Delete a loan permanently."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.loans_delete(loan_id=loan_id),
    )
    return _ok(result)


@mcp.tool()
def loans_list_by_property(
    immobilie_id,
    token,
    organisation_id,
    base_url=None,
):
    """List all loans for a specific property."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.loans_list_by_property(immobilie_id=immobilie_id),
    )
    return _ok(result)


@mcp.tool()
def loans_outstanding(
    loan_ids,
    token,
    organisation_id,
    base_url=None,
):
    """Calculate outstanding amounts for the given loan IDs."""

    ids = _require_list(field_name='loan_ids', value=loan_ids)
    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.loans_outstanding(loan_ids=ids),
    )
    return _ok(result)
