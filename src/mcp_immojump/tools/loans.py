from .._shared import _call_with_client, _ok, _require_dict, _require_list, destructive_op, read_only, write_op


def register(mcp):
    @mcp.tool(annotations=read_only())
    def loans_list(
        token=None,
        organisation_id=None,
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
        - immobilie_id: property ID (UUID string)
        - principal: loan amount in EUR, e.g. 250000
        - interest_rate: nominal rate as a FRACTION, not percent:
          3.5 % = 0.035, 0 % allowed. Values >= 0.25 are rejected (400).
        - amortization_rate: initial repayment as a fraction (2 % = 0.02)
        - start_date: date string "YYYY-MM-DD", e.g. "2026-01-01"
          (full datetimes are auto-truncated to date)

        Optional:
        - name: string, e.g. "Sparkasse Hauptdarlehen"
        - bank_name: string
        - amortization_start_date: date string "YYYY-MM-DD" (if repayment
          starts later than start_date)
        - fixed_rate_years: integer (Zinsbindung)
        - term_years: integer
        - payment_frequency_months: integer, default 1 (monthly)

        Invalid or missing values answer 400 with a German `message` and the
        offending fields under `errors`.
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

        loan_id: loan ID (UUID string) as returned by loans_create/loans_list.
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
        loan_ids,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Calculate outstanding amounts for the given loan IDs.

        loan_ids: list of integer loan IDs, e.g. [1, 2, 3].
        """

        ids = _require_list(field_name='loan_ids', value=loan_ids)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.loans_outstanding(loan_ids=ids),
        )
        return _ok(result)
