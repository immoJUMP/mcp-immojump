"""Client tests for Pipeline domain: deals, tickets (pipelines/statuses/templates already covered)."""

import json

import httpx

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
        client.deals_create(data={'pipeline_id': 'p-1', 'status_id': 's-1'})

    assert captured['json']['organisation_id'] == 'org-1'
    assert captured['json']['pipeline_id'] == 'p-1'


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


def test_tickets_create_includes_org():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.tickets_create(data={'title': 'Bug', 'priority': 'high'})

    assert captured['json']['organisation_id'] == 'org-1'
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
