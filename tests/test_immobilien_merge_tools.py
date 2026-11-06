"""Tool surface for merging duplicate properties (immo-calc#2108).

The backend schemas reject unknown keys with 400, so the tools may only send
the documented keys. The descriptions have to steer an agent through the safe
order: preview first, duplicates go to the trash, the merge can be undone.
"""

from __future__ import annotations

import json

import httpx
import pytest

import mcp_immojump.tools.immobilien as immobilien_tools
from mcp_immojump.client import ImmojumpAPIClient, ImmojumpCredentials

MERGE_TOOLS = (
    'immobilien_merge_preview',
    'immobilien_merge',
    'immobilien_merge_logs',
    'immobilien_merge_restore',
)


def _servers():
    from mcp_immojump.server import mcp as full
    from mcp_immojump.servers.profi import mcp as profi
    from mcp_immojump.servers.properties import mcp as properties
    from mcp_immojump.servers.standard import mcp as standard
    return {'standard': standard, 'profi': profi, 'properties': properties, 'full': full}


@pytest.fixture(scope='module')
def tools():
    from mcp_immojump.server import mcp
    return dict(mcp._tool_manager._tools.items())


@pytest.fixture
def captured(monkeypatch):
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={'success': True})

    def fake_call_with_client(*, base_url, token, organisation_id, callback):
        creds = ImmojumpCredentials(base_url='http://localhost:8081', token='tok', organisation_id='org-1')
        with ImmojumpAPIClient(creds, transport=httpx.MockTransport(handler)) as client:
            return callback(client)

    monkeypatch.setattr(immobilien_tools, '_call_with_client', fake_call_with_client)
    return requests


@pytest.mark.parametrize('server_name', ['standard', 'profi', 'properties', 'full'])
def test_every_server_with_property_tools_offers_the_merge(server_name):
    names = set(_servers()[server_name]._tool_manager._tools)
    assert set(MERGE_TOOLS) <= names


def test_annotations_mark_the_merge_as_destructive_and_the_preview_as_read_only(tools):
    assert tools['immobilien_merge_preview'].annotations.readOnlyHint is True
    assert tools['immobilien_merge_logs'].annotations.readOnlyHint is True
    assert tools['immobilien_merge'].annotations.destructiveHint is True
    assert tools['immobilien_merge_restore'].annotations.readOnlyHint is False


def test_merge_description_demands_the_preview_and_names_trash_and_undo(tools):
    description = tools['immobilien_merge'].description
    assert 'immobilien_merge_preview' in description
    assert 'trash' in description
    assert 'immobilien_merge_restore' in description
    assert 'immobilien_merge' in tools['immobilien_merge_preview'].description


def test_merge_description_names_every_field_and_block(tools):
    description = tools['immobilien_merge'].description
    for key in ('name', 'type', 'status_id', 'adresse', 'baujahr', 'grundstueck', 'asking_price',
                'acquisition_price', 'sale_price', 'target_sale_price',
                'einheiten', 'kalkulation', 'finanzierung'):
        assert key in description, key


def test_preview_sends_the_ids_and_the_primary(tools, captured):
    tools['immobilien_merge_preview'].fn(immobilie_ids=['a', 'b'], primary_id='b')

    [request] = captured
    assert request.method == 'POST'
    assert request.url.path == '/api/v2/immobilien/merge/preview'
    assert json.loads(request.read()) == {'immobilie_ids': ['a', 'b'], 'primary_id': 'b'}


def test_preview_leaves_the_primary_to_the_backend(tools, captured):
    tools['immobilien_merge_preview'].fn(immobilie_ids='["a", "b"]')

    [request] = captured
    assert json.loads(request.read()) == {'immobilie_ids': ['a', 'b']}


def test_merge_sends_exactly_the_schema_keys(tools, captured):
    tools['immobilien_merge'].fn(
        primary_id='a',
        duplicate_ids=['b'],
        field_choices={'name': 'b'},
        block_choices='{"einheiten": "b"}',
        include_documents='false',
    )

    [request] = captured
    assert request.method == 'POST'
    assert request.url.path == '/api/v2/immobilien/merge'
    assert json.loads(request.read()) == {
        'primary_id': 'a',
        'duplicate_ids': ['b'],
        'field_choices': {'name': 'b'},
        'block_choices': {'einheiten': 'b'},
        'include_documents': False,
    }


def test_merge_defaults_take_documents_along(tools, captured):
    tools['immobilien_merge'].fn(primary_id='a', duplicate_ids='b,c')

    [request] = captured
    assert json.loads(request.read()) == {
        'primary_id': 'a',
        'duplicate_ids': ['b', 'c'],
        'field_choices': {},
        'block_choices': {},
        'include_documents': True,
    }


def test_merge_requires_the_primary(tools, captured):
    with pytest.raises(ValueError, match='primary_id'):
        tools['immobilien_merge'].fn(primary_id='', duplicate_ids=['b'])
    assert captured == []


def test_logs_scope_the_organisation(tools, captured):
    tools['immobilien_merge_logs'].fn()

    [request] = captured
    assert request.method == 'GET'
    assert request.url.path == '/api/v2/immobilien/merge/logs'
    assert request.url.params['organisation_id'] == 'org-1'


def test_restore_posts_to_the_log(tools, captured):
    tools['immobilien_merge_restore'].fn(log_id='log-1')

    [request] = captured
    assert request.method == 'POST'
    assert request.url.path == '/api/v2/immobilien/merge/logs/log-1/restore'
    assert request.read() == b''
