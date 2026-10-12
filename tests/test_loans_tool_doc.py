"""loans_create/loans_update nennen die Felder, die das Backend liest.

Die alte Doku nannte `loan_amount`/`repayment_rate` (Backend: `principal`/
`amortization_rate`) und den Zins „in Prozent, z. B. 3.5" — das Backend
erwartet einen Anteil (0.035). Ein Agent, der der Doku folgte, legte ein
Darlehen mit 350 % Zins an (seit immo-calc PR „fix(loans)" lehnt das Backend
Zinssätze ab 0.25 mit 400 ab).
"""
from mcp_immojump.server import mcp


def _doc(name):
    return mcp._tool_manager._tools[name].description


def test_loans_create_nennt_backend_felder():
    doc = _doc('loans_create')
    for feld in ('principal', 'interest_rate', 'amortization_rate', 'start_date', 'immobilie_id'):
        assert feld in doc
    for alt in ('loan_amount', 'repayment_rate', 'percent, e.g. 3.5', 'integer ID of the property'):
        assert alt not in doc
    assert '0.035' in doc


def test_loans_update_verweist_auf_dieselben_felder():
    doc = _doc('loans_update')
    assert 'loans_create' in doc
    assert 'integer ID of the loan' not in doc
