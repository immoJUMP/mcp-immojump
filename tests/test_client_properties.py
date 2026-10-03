"""Client tests for Properties domain: immobilien, units, loans, milestones, documents, valuation."""

import json

import httpx

from mcp_immojump.client import ImmojumpAPIClient, ImmojumpCredentials


def _creds():
    return ImmojumpCredentials(base_url='http://localhost:8081', token='tok', organisation_id='org-1')


def _capture_client(handler):
    transport = httpx.MockTransport(handler)
    return ImmojumpAPIClient(_creds(), transport=transport)


# ---------------------------------------------------------------------------
# Immobilien
# ---------------------------------------------------------------------------

def test_immobilien_list_path_and_params():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json={'items': []})

    with _capture_client(handler) as client:
        client.immobilien_list(page=2, per_page=10)

    assert captured['path'] == '/api/v2/immobilien'
    assert captured['params']['organisation_id'] == 'org-1'
    assert captured['params']['page'] == '2'
    assert captured['params']['per_page'] == '10'


def test_immobilien_search_passes_filters():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json={'items': []})

    with _capture_client(handler) as client:
        client.immobilien_search(search='Berlin', status_ids=['s1', 's2'], tag_ids=['t1'])

    assert captured['path'] == '/api/v2/immobilien/search'
    assert captured['params']['search'] == 'Berlin'
    assert captured['params']['status_ids'] == 's1,s2'
    assert captured['params']['tag_ids'] == 't1'


def test_immobilien_get_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        captured['method'] = req.method
        return httpx.Response(200, json={'id': 'imm-1'})

    with _capture_client(handler) as client:
        client.immobilien_get(immobilie_id='imm-1')

    assert captured['path'] == '/api/v2/immobilien/imm-1'
    assert captured['method'] == 'GET'


def test_immobilien_create_sends_json_with_org():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={'id': 'new-1'})

    with _capture_client(handler) as client:
        client.immobilien_create(data={'title': 'Test', 'kaufpreis': 100000})

    assert captured['method'] == 'POST'
    assert captured['json']['title'] == 'Test'
    assert captured['json']['organisation_id'] == 'org-1'


def test_immobilien_patch_method_and_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.immobilien_patch(immobilie_id='imm-1', data={'kaufpreis': 200000})

    assert captured['method'] == 'PATCH'
    assert captured['path'] == '/api/v2/immobilien/imm-1'
    assert captured['json']['kaufpreis'] == 200000


def test_immobilien_delete_method():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.immobilien_delete(immobilie_id='imm-1')

    assert captured['method'] == 'DELETE'
    assert captured['path'] == '/api/v2/immobilien/imm-1'


def test_immobilien_duplicate_post():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={'id': 'dup-1'})

    with _capture_client(handler) as client:
        client.immobilien_duplicate(immobilie_id='imm-1')

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/v2/immobilien/imm-1/duplicate'


def test_immobilien_transfer_body():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.immobilien_transfer(immobilie_id='imm-1', target_organisation_id='org-2')

    assert captured['path'] == '/api/v2/immobilien/imm-1/transfer'
    assert captured['json']['target_organisation_id'] == 'org-2'


def test_immobilien_update_status_sends_only_the_status_id():
    """PUT /api/v2/immobilien/<id> reads nothing but status_id.

    The former immobilien_update sent a whole property object there: every
    field was dropped, and without status_id the backend cleared the status.
    """
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={'id': 'imm-1'})

    with _capture_client(handler) as client:
        client.immobilien_update_status(immobilie_id='imm-1', status_id='42')

    assert captured['method'] == 'PUT'
    assert captured['path'] == '/api/v2/immobilien/imm-1'
    assert captured['json'] == {'status_id': 42}


def test_immobilien_update_status_none_takes_the_property_out_of_the_pipeline():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={'id': 'imm-1'})

    with _capture_client(handler) as client:
        client.immobilien_update_status(immobilie_id='imm-1', status_id=None)

    # An explicit null — a missing key is rejected with HTTP 400.
    assert captured['json'] == {'status_id': None}


def test_immobilien_split_units_sends_unit_ids_and_target_type():
    """Without unit_ids the backend answers 400 — the tool used to send no body at all."""
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json=[])

    with _capture_client(handler) as client:
        client.immobilien_split_units(immobilie_id='imm-1', unit_ids=['u-1', 'u-2'], target_type='ETW')

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/v2/immobilien/imm-1/split-units'
    assert captured['json'] == {'unit_ids': ['u-1', 'u-2'], 'target_type': 'ETW'}


def test_immobilien_split_units_leaves_the_default_type_to_the_backend():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json=[])

    with _capture_client(handler) as client:
        client.immobilien_split_units(immobilie_id='imm-1', unit_ids=['u-1'])

    assert captured['json'] == {'unit_ids': ['u-1']}


def test_immobilien_contacts_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.immobilien_contacts(immobilie_id='imm-1')

    assert captured['path'] == '/api/v2/immobilien/imm-1/contacts'


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------

def test_units_list_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.units_list(immobilie_id='imm-1')

    assert captured['path'] == '/api/units/immobilie/imm-1/units'


def test_units_create_path_and_body():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.units_create(immobilie_id='imm-1', data={'name': 'WE1', 'wohnflaeche': 60})

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/units/unit/imm-1'
    assert captured['json']['name'] == 'WE1'


def test_units_update_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.units_update(unit_id='u-1', data={'wohnflaeche': 80})

    assert captured['method'] == 'PUT'
    assert captured['path'] == '/api/units/unit/u-1'


def test_units_delete_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.units_delete(unit_id='u-1')

    assert captured['method'] == 'DELETE'
    assert captured['path'] == '/api/units/unit/u-1'


# ---------------------------------------------------------------------------
# Loans
# ---------------------------------------------------------------------------

def test_loans_list_sends_org_param():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.loans_list()

    assert captured['params']['organisation_id'] == 'org-1'


def test_loans_create_body():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.loans_create(data={'immobilie_id': 'imm-1', 'loan_amount': 200000})

    assert captured['json']['immobilie_id'] == 'imm-1'
    assert captured['json']['organisation_id'] == 'org-1'


def test_loans_list_by_property_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.loans_list_by_property(immobilie_id='imm-1')

    assert captured['path'] == '/api/immobilien/imm-1/loans'


def test_loans_outstanding_body():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.loans_outstanding(loan_ids=['l1', 'l2'])

    assert captured['json']['loan_ids'] == ['l1', 'l2']


# ---------------------------------------------------------------------------
# Milestones
# ---------------------------------------------------------------------------

def test_milestones_list_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.milestones_list(immobilie_id='imm-1')

    assert captured['path'] == '/api/milestones/immobilie/imm-1'


def test_milestones_create_path_and_body():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.milestones_create(immobilie_id='imm-1', data={'type': 'BNL', 'date': '2026-06-15'})

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/milestones/immobilie/imm-1'
    assert captured['json']['type'] == 'BNL'


def test_milestones_update_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.milestones_update(milestone_id='ms-1', data={'status': 'DONE'})

    assert captured['method'] == 'PUT'
    assert captured['path'] == '/api/milestones/ms-1'


def test_milestones_delete_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.milestones_delete(milestone_id='ms-1')

    assert captured['method'] == 'DELETE'
    assert captured['path'] == '/api/milestones/ms-1'


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

def test_documents_list_with_immobilie_filter():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.documents_list(immobilie_id='imm-1')

    assert captured['path'] == '/api/documents/documents'
    assert captured['params']['immobilie_id'] == 'imm-1'


def test_documents_rename_path_and_body():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.documents_rename(document_id='doc-1', name='New Name.pdf')

    assert captured['method'] == 'PUT'
    assert captured['path'] == '/api/documents/documents/doc-1/rename'
    assert captured['json']['name'] == 'New Name.pdf'


def test_documents_analyze_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.documents_analyze(document_id='doc-1')

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/documents/documents/doc-1/analyze'


def test_documents_mark_reviewed_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.documents_mark_reviewed(document_id='doc-1')

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/documents/documents/doc-1/mark-reviewed'


# ---------------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------------

def test_valuation_request_sends_only_the_property_id():
    """The backend reads address, living space, type and year from the property.

    The old body (``organisation_id`` + ``providers`` list) never matched the
    backend schema, which answered every call with a 400.
    """
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.valuation_request(immobilie_id='imm-1')

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/valuation/request'
    assert captured['json'] == {'immobilie_id': 'imm-1'}


def test_valuation_request_passes_provider_and_refresh():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.valuation_request(immobilie_id='imm-1', provider='fpre', force_refresh=True)

    assert captured['json'] == {'immobilie_id': 'imm-1', 'provider': 'fpre', 'force_refresh': True}


def test_valuation_history_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.valuation_history(immobilie_id='imm-1')

    assert captured['path'] == '/api/valuation/history/imm-1'


def test_valuation_providers_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.valuation_providers()

    assert captured['path'] == '/api/valuation/providers'


def test_property_intelligence_uses_shared_authorised_backend_routes():
    captured = []

    def handler(req):
        captured.append((req.method, req.url.path, json.loads(req.read()) if req.read() else None))
        return httpx.Response(200, json={"profile_match": {"status": "unknown"}})

    with _capture_client(handler) as client:
        client.property_intelligence_get(immobilie_id="imm-1")
        client.property_intelligence_settings(immobilie_id="imm-1", data={"phase": "purchase"})
        client.property_intelligence_decide(
            immobilie_id="imm-1",
            data={
                "outcome": "reject",
                "reason": "renovation",
                "request_id": "00000000-0000-0000-0000-000000000002",
            },
        )
        client.property_intelligence_analyze(immobilie_id="imm-1")
    assert captured[0] == ("GET", "/api/immobilien/imm-1/intelligence", None)
    assert captured[1] == (
        "PUT",
        "/api/immobilien/imm-1/intelligence/settings",
        {"phase": "purchase"},
    )
    assert captured[2][0:2] == ("POST", "/api/immobilien/imm-1/intelligence/decisions")
    assert captured[2][2]["request_id"] == "00000000-0000-0000-0000-000000000002"
    assert captured[3][0:2] == ("POST", "/api/immobilien/imm-1/intelligence/analyze")
