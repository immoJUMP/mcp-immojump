"""Client tests for Investor domain."""

import json

import httpx

from mcp_immojump.client import ImmojumpAPIClient, ImmojumpCredentials


def _creds():
    return ImmojumpCredentials(base_url='http://localhost:8081', token='tok', organisation_id='org-1')


def _capture_client(handler):
    transport = httpx.MockTransport(handler)
    return ImmojumpAPIClient(_creds(), transport=transport)


# ---------------------------------------------------------------------------
# Search Profiles
# ---------------------------------------------------------------------------

def test_investor_search_profile_get_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.investor_search_profile_get(org_id='org-1')

    assert captured['path'] == '/api/organisations/org-1/search-profile'


def test_investor_search_profile_save_method():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.investor_search_profile_save(org_id='org-1', data={'min_kaufpreis': 100000})

    assert captured['method'] == 'PUT'
    assert captured['path'] == '/api/organisations/org-1/search-profile'


def test_investor_search_profile_submissions_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.investor_search_profile_submissions(org_id='org-1')

    assert captured['path'] == '/api/organisations/org-1/search-profile-submissions'


# ---------------------------------------------------------------------------
# Search Profile Masks
# ---------------------------------------------------------------------------

def test_investor_search_profile_masks_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.investor_search_profile_masks(org_id='org-1')

    assert captured['path'] == '/api/organisations/org-1/search-profile-masks'


def test_investor_search_profile_mask_delete_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.investor_search_profile_mask_delete(org_id='org-1', mask_id='mask-1')

    assert captured['method'] == 'DELETE'
    assert captured['path'] == '/api/organisations/org-1/search-profile-masks/mask-1'


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------

def test_investor_assignments_list_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.investor_assignments_list(org_id='org-1')

    assert captured['path'] == '/api/organisations/org-1/investor-assignments'


def test_investor_assignments_create_body():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        captured['path'] = req.url.path
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.investor_assignments_create(
            org_id='org-1', data={'immobilie_id': 'imm-1', 'user_id': 'u-1'},
        )

    assert captured['path'] == '/api/organisations/org-1/investor-assignments'
    assert captured['json']['immobilie_id'] == 'imm-1'


def test_investor_assignment_update_uses_patch():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.investor_assignment_update(
            org_id='org-1', assignment_id='a-1', data={'status': 'accepted'},
        )

    assert captured['method'] == 'PATCH'
    assert captured['path'] == '/api/organisations/org-1/investor-assignments/a-1'


def test_investor_my_assignments_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.investor_my_assignments(org_id='org-1')

    assert captured['path'] == '/api/organisations/org-1/my-assignments'


def test_investor_my_assignment_favorite_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.investor_my_assignment_favorite(org_id='org-1', assignment_id='a-1')

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/organisations/org-1/my-assignments/a-1/favorite'


def test_investor_my_assignment_accept_agreement_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.investor_my_assignment_accept_agreement(org_id='org-1', assignment_id='a-1')

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/organisations/org-1/my-assignments/a-1/accept-agreement'


# ---------------------------------------------------------------------------
# Matching Config & Finance Defaults
# ---------------------------------------------------------------------------

def test_investor_matching_config_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.investor_matching_config(org_id='org-1')

    assert captured['path'] == '/api/organisations/org-1/matching-config'


def test_investor_matching_config_reset_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.investor_matching_config_reset(org_id='org-1')

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/organisations/org-1/matching-config/reset'


def test_investor_finance_defaults_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.investor_finance_defaults(org_id='org-1')

    assert captured['path'] == '/api/organisations/org-1/investor-finance-defaults'


def test_investor_legal_docs_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.investor_legal_docs(org_id='org-1')

    assert captured['path'] == '/api/organisations/org-1/legal-docs'


def test_investor_reporting_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.investor_reporting(org_id='org-1')

    assert captured['path'] == '/api/organisations/org-1/investor-reporting'
