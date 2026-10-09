"""Client tests for Pipeline domain: deals, tickets (pipelines/statuses/templates already covered)."""

import json

import httpx
import pytest

from mcp_immojump.client import ImmojumpAPIClient, ImmojumpCredentials


def _creds():
    return ImmojumpCredentials(base_url='http://localhost:8081', token='tok', organisation_id='org-1')


def _capture_client(handler):
    transport = httpx.MockTransport(handler)
    return ImmojumpAPIClient(_creds(), transport=transport)


# ---------------------------------------------------------------------------
# Deals
# ---------------------------------------------------------------------------

def test_deals_list_path_and_params():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.deals_list(pipeline_id='p-1', status_id='s-1', search='Berlin')

    assert captured['path'] == '/api/deals'
    assert captured['params']['pipeline_id'] == 'p-1'
    assert captured['params']['status_id'] == 's-1'
    assert captured['params']['search'] == 'Berlin'


def test_deals_list_sends_no_pagination():
    """/api/deals is not paginated — sending page/per_page would suggest a
    capped result that the backend never applies."""
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.deals_list()

    assert captured['params'] == {'organisation_id': 'org-1'}


def test_deals_list_tool_has_no_pagination_args():
    import inspect

    from mcp_immojump.server import mcp

    fn = mcp._tool_manager._tools['deals_list'].fn
    params = inspect.signature(fn).parameters
    assert 'page' not in params
    assert 'per_page' not in params
    assert {'pipeline_id', 'status_id', 'search'} <= set(params)


def test_deals_get_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.deals_get(deal_id='d-1')

    assert captured['path'] == '/api/deals/d-1'


def test_deals_create_includes_org():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.deals_create(data={'name': 'MFH Kaiserstr.', 'status_id': 7})

    assert captured['json'] == {'organisation_id': 'org-1', 'name': 'MFH Kaiserstr.', 'status_id': 7}


def _sent_deal_payload(method, data):
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        if method == 'create':
            client.deals_create(data=data)
        else:
            client.deals_update(deal_id='d-1', data=data)
    return captured.get('json')


@pytest.mark.parametrize('method', ['create', 'update'])
def test_deals_legacy_field_names_are_mapped_to_backend_fields(method):
    """Until 10/2026 the tool docstring advertised title/value/notes and
    singular immobilie_id/contact_id. The backend's DealSchema rejects all of
    them with 400, so agents following old prompts must still land."""
    sent = _sent_deal_payload(method, {
        'title': 'MFH Kaiserstr.',
        'value': 450000,
        'notes': 'Exposé angefragt',
        'immobilie_id': 'imm-1',
        'contact_id': 'c-1',
    })

    assert sent['name'] == 'MFH Kaiserstr.'
    assert sent['deal_amount'] == 450000
    assert sent['description'] == 'Exposé angefragt'
    assert sent['immobilie_ids'] == ['imm-1']
    assert sent['contact_ids'] == ['c-1']
    for legacy in ('title', 'value', 'notes', 'immobilie_id', 'contact_id'):
        assert legacy not in sent


@pytest.mark.parametrize('method', ['create', 'update'])
def test_deals_singular_id_null_clears_the_list(method):
    sent = _sent_deal_payload(method, {'immobilie_id': None, 'contact_id': None})

    assert sent['immobilie_ids'] == []
    assert sent['contact_ids'] == []


@pytest.mark.parametrize('method', ['create', 'update'])
def test_deals_legacy_name_equal_to_real_field_is_accepted(method):
    sent = _sent_deal_payload(method, {'name': 'A', 'title': 'A', 'contact_ids': ['c-1'], 'contact_id': 'c-1'})

    assert sent['name'] == 'A'
    assert sent['contact_ids'] == ['c-1']
    assert 'title' not in sent and 'contact_id' not in sent


@pytest.mark.parametrize('method', ['create', 'update'])
@pytest.mark.parametrize('data', [
    {'name': 'A', 'title': 'B'},
    {'deal_amount': 1, 'value': 2},
    {'immobilie_ids': ['imm-1'], 'immobilie_id': 'imm-2'},
    {'contact_ids': ['c-1', 'c-2'], 'contact_id': 'c-1'},
])
def test_deals_conflicting_legacy_and_real_field_is_rejected(method, data):
    """Never silently drop one of two contradicting values."""
    with pytest.raises(ValueError, match='widersprüchlich'):
        _sent_deal_payload(method, data)


@pytest.mark.parametrize('method', ['create', 'update'])
def test_deals_pipeline_id_is_rejected_with_status_hint(method):
    """A deal has no pipeline field — the pipeline follows from status_id.
    Mapping is impossible (which status?), dropping would hide the intent."""
    with pytest.raises(ValueError, match='status_id'):
        _sent_deal_payload(method, {'name': 'A', 'pipeline_id': 3})


def test_deals_create_does_not_mutate_input():
    original = {'title': 'A', 'immobilie_id': 'imm-1'}
    _sent_deal_payload('create', original)
    assert original == {'title': 'A', 'immobilie_id': 'imm-1'}


def test_deals_update_uses_patch():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.deals_update(deal_id='d-1', data={'status_id': 's-2'})

    assert captured['method'] == 'PATCH'
    assert captured['path'] == '/api/deals/d-1'


# ---------------------------------------------------------------------------
# Tickets
# ---------------------------------------------------------------------------

def test_tickets_statuses_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.tickets_statuses()

    assert captured['path'] == '/api/tickets/statuses'
    assert captured['params']['organisation_id'] == 'org-1'


def test_tickets_list_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.tickets_list(status='open')

    assert captured['path'] == '/api/tickets'


def test_tickets_list_sends_backend_filter_names():
    """Backend (GET /api/tickets) reads exactly `status` and `search`."""
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json={'items': [], 'total': 0, 'page': 2, 'per_page': 10})

    with _capture_client(handler) as client:
        client.tickets_list(page=2, per_page=10, status='in_progress', search='Heizung')

    assert captured['params'] == {
        'organisation_id': 'org-1',
        'page': '2',
        'per_page': '10',
        'status': 'in_progress',
        'search': 'Heizung',
    }


def test_tickets_create_excludes_org_from_body():
    """Ticket backend reads org from X-Organisation-Id header, not body."""
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        captured['x_org'] = req.headers.get('X-Organisation-Id')
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.tickets_create(data={'title': 'Bug', 'priority': 'high'})

    assert 'organisation_id' not in captured['json']  # NOT in body
    assert captured['x_org'] == 'org-1'  # in header
    assert captured['json']['title'] == 'Bug'


def test_tickets_change_status_sends_status_id():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.tickets_change_status(ticket_id='t-1', status_id='s-done')

    assert captured['method'] == 'PATCH'
    assert captured['path'] == '/api/tickets/t-1/status'
    assert captured['json'] == {'status_id': 's-done'}


def test_tickets_list_comments_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.tickets_list_comments(ticket_id='t-1')

    assert captured['path'] == '/api/tickets/t-1/activities'


def test_tickets_add_comment_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.tickets_add_comment(ticket_id='t-1', data={'text': 'Fixed it'})

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/tickets/t-1/activities'
