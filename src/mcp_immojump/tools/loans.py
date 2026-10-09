from .._shared import _call_with_client, _id_list, _ok, _require_dict, destructive_op, read_only, write_op


def register(mcp):
    @mcp.tool(annotations=read_only())
    def loans_list(
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List all loans of the properties in the organisation."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.loans_list(),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def loans_create(
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create a new loan.

        data: JSON object with:

        Required:
        - immobilie_id: integer ID of the property
        - loan_amount: number (EUR)
        - interest_rate: number (percent, e.g. 3.5)
        - start_date: date string "YYYY-MM-DD", e.g. "2026-01-01"
          (full datetimes are auto-truncated to date)

        Optional:
        - bank_name: string
        - repayment_rate: number (percent, e.g. 2.0)
        - term_years: integer
        - amortization_start_date: date string "YYYY-MM-DD" (if repayment
          starts later than start_date)
        - type: annuity, bullet, or endfaellig
        - notes: string
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.loans_create(data=payload),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def loans_update(
        loan_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Update an existing loan (partial — only provided fields change).

        loan_id: integer ID of the loan.
        data: same fields as loans_create. Date fields accept "YYYY-MM-DD" format.
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.loans_update(loan_id=loan_id, data=payload),
        )
        return _ok(result)

    @mcp.tool(annotations=destructive_op())
    def loans_delete(
        loan_id,
        token=None,
        organisation_id=None,
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

    @mcp.tool(annotations=read_only())
    def loans_list_by_property(
        immobilie_id,
        token=None,
        organisation_id=None,
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

    @mcp.tool(annotations=read_only())
    def loans_outstanding(
        immobilie_ids,
        as_of=None,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Outstanding loan balance per property, summed over all its loans.

        - immobilie_ids: list of property IDs (not loan IDs). Properties the
          caller may not access are skipped without an error.
        - as_of: optional date "YYYY-MM-DD" (default: today)

        Returns {"per_immobilie": {<immobilie_id>: amount}, "total": amount,
        "as_of": "YYYY-MM-DD"} in EUR.
        """

        ids = _id_list(field_name='immobilie_ids', value=immobilie_ids)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.loans_outstanding(immobilie_ids=ids, as_of=as_of),
        )
        return _ok(result)
