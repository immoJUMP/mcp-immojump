"""Client tests for CRM domain: contacts CRUD, activities, tags."""

import json

import httpx

from mcp_immojump.client import ImmojumpAPIClient, ImmojumpCredentials


def _creds():
    return ImmojumpCredentials(base_url='http://localhost:8081', token='tok', organisation_id='org-1')


def _capture_client(handler):
    transport = httpx.MockTransport(handler)
    return ImmojumpAPIClient(_creds(), transport=transport)


# ---------------------------------------------------------------------------
# Contacts CRUD
# ---------------------------------------------------------------------------

def test_contacts_list_path_and_params():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.contacts_list(page=3, per_page=50, search='Müller')

    assert captured['path'] == '/api/contacts'
    assert captured['params']['organisation_id'] == 'org-1'
    assert captured['params']['page'] == '3'
    assert captured['params']['search'] == 'Müller'


def test_contacts_get_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.contacts_get(contact_id='c-1')

    assert captured['path'] == '/api/contacts/c-1'


def test_contacts_create_includes_org():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.contacts_create(data={'first_name': 'Max', 'last_name': 'Mustermann'})

    assert captured['json']['organisation_id'] == 'org-1'
    assert captured['json']['first_name'] == 'Max'


def test_contacts_update_path_and_method():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.contacts_update(contact_id='c-1', data={'first_name': 'Moritz'})

    assert captured['method'] == 'PUT'
    assert captured['path'] == '/api/contacts/c-1'


def test_contacts_update_status_sends_status_id_as_int():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.contacts_update_status(contact_id='c-1', status_id='42')

    assert captured['path'] == '/api/contacts/c-1/status'
    assert captured['json'] == {'status_id': 42}


def test_contacts_delete_method():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.contacts_delete(contact_id='c-1')

    assert captured['method'] == 'DELETE'
    assert captured['path'] == '/api/contacts/c-1'


def test_contacts_count_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json={'count': 5})

    with _capture_client(handler) as client:
        client.contacts_count()

    assert captured['path'] == '/api/contacts/count'
    assert captured['params']['organisation_id'] == 'org-1'


def test_contacts_bulk_delete_body():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.contacts_bulk_delete(contact_ids=['c-1', 'c-2'])

    assert captured['json']['contact_ids'] == ['c-1', 'c-2']


def test_contacts_get_immobilien_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.contacts_get_immobilien(contact_id='c-1')

    assert captured['path'] == '/api/contacts/c-1/immobilien'


def test_contacts_merge_restore_body():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.contacts_merge_restore(merge_id='m-1')

    assert captured['json']['merge_id'] == 'm-1'


# ---------------------------------------------------------------------------
# Activities
# ---------------------------------------------------------------------------

def test_activities_list_path_and_params():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.activities_list(status='open', type='call')

    assert captured['path'] == '/api/activities/activities'
    assert captured['params']['status'] == 'open'
    assert captured['params']['type'] == 'call'


def test_activities_create_includes_org():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.activities_create(data={'title': 'Anruf', 'type': 'call'})

    assert captured['json']['organisation_id'] == 'org-1'
    assert captured['json']['title'] == 'Anruf'


def test_activities_create_for_property_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.activities_create_for_property(immobilie_id='imm-1', data={'title': 'Besichtigung'})

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/activities/activities/immobilie/imm-1'


def test_activities_update_method_and_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.activities_update(activity_id='a-1', data={'status': 'done'})

    assert captured['method'] == 'PUT'
    assert captured['path'] == '/api/activities/activities/a-1'


def test_activities_list_by_property_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.activities_list_by_property(immobilie_id='imm-1')

    assert captured['path'] == '/api/activities/activities/immobilie/imm-1'


def test_activities_statistics_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.activities_statistics()

    assert captured['path'] == '/api/activities/activities/statistics'


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

def test_tags_list_uses_for_param():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.tags_list(entity_type='immobilie')

    assert captured['path'] == '/api/org-1/tags'
    assert captured['params']['for'] == 'immobilie'


def test_tags_create_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.tags_create(data={'name': 'Neubau', 'color': '#ff0000'})

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/org-1/tags'


def test_tags_update_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.tags_update(tag_id='tag-1', data={'name': 'Altbau'})

    assert captured['method'] == 'PUT'
    assert captured['path'] == '/api/org-1/tags/tag-1'


def test_tags_delete_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.tags_delete(tag_id='tag-1')

    assert captured['method'] == 'DELETE'
    assert captured['path'] == '/api/tags/tag-1'


def test_tags_get_entity_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.tags_get_entity(entity_type='immobilie', entity_id='imm-1')

    assert captured['path'] == '/api/tags/immobilie/imm-1'


def test_tags_update_entity_sends_raw_array():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        captured['body'] = json.loads(req.read())
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.tags_update_entity(entity_type='immobilie', entity_id='imm-1', tag_ids=['t1', 't2'])

    assert captured['method'] == 'PUT'
    assert captured['path'] == '/api/tags/immobilie/imm-1'
    assert captured['body'] == ['t1', 't2']  # raw array, NOT {"tag_ids": [...]}
