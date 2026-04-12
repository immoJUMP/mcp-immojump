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


def test_immobilien_split_units_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.immobilien_split_units(immobilie_id='imm-1')

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/v2/immobilien/imm-1/split-units'


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

def test_valuation_request_body():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.valuation_request(immobilie_id='imm-1', providers=['sprengnetter'])

    assert captured['method'] == 'POST'
    assert captured['json']['immobilie_id'] == 'imm-1'
    assert captured['json']['organisation_id'] == 'org-1'
    assert captured['json']['providers'] == ['sprengnetter']


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
