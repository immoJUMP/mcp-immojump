"""Tool surface for moving a property in the pipeline and splitting an MFH.

``immobilien_update`` promised a full update via PUT. The backend's PUT reads
nothing but ``status_id``: every field change was dropped, and a body without
``status_id`` cleared the pipeline status. ``immobilien_update_status`` says
what the route does; field changes go through ``immobilien_patch``.

``immobilien_split_units`` posted without a body, so the backend rejected
every call (``unit_ids`` is required).
"""

from __future__ import annotations

import json

import httpx
import pytest

import mcp_immojump.tools.immobilien as immobilien_tools
from mcp_immojump.client import ImmojumpAPIClient, ImmojumpCredentials

PROPERTY_TYPE_CODES = ('ETW', 'EFH', 'MFH', 'WGH', 'GEW', 'Sonstiges')


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
    """Run the tool's callback against a mock transport and record the request."""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={'id': 'imm-1'})

    def fake_call_with_client(*, base_url, token, organisation_id, callback):
        creds = ImmojumpCredentials(base_url='http://localhost:8081', token='tok', organisation_id='org-1')
        with ImmojumpAPIClient(creds, transport=httpx.MockTransport(handler)) as client:
            return callback(client)

    monkeypatch.setattr(immobilien_tools, '_call_with_client', fake_call_with_client)
    return requests


@pytest.mark.parametrize('server_name', ['standard', 'profi', 'properties', 'full'])
def test_every_server_with_property_tools_offers_update_status_instead_of_update(server_name):
    names = set(_servers()[server_name]._tool_manager._tools)
    assert 'immobilien_patch' in names
    assert 'immobilien_update_status' in names
    assert 'immobilien_update' not in names


def test_update_status_sends_only_the_status_id(tools, captured):
    result = tools['immobilien_update_status'].fn(immobilie_id='imm-1', status_id=7)

    assert result['ok'] is True
    [request] = captured
    assert request.method == 'PUT'
    assert request.url.path == '/api/v2/immobilien/imm-1'
    assert json.loads(request.read()) == {'status_id': 7}


def test_update_status_with_null_takes_the_property_out_of_the_pipeline(tools, captured):
    tools['immobilien_update_status'].fn(immobilie_id='imm-1', status_id=None)

    [request] = captured
    assert json.loads(request.read()) == {'status_id': None}


def test_update_status_requires_the_status_id(tools):
    required = tools['immobilien_update_status'].parameters.get('required', [])
    assert {'immobilie_id', 'status_id'} <= set(required)


def test_patch_and_update_status_point_at_each_other(tools):
    """PATCH files status_id away into the property data; the status stays put."""
    assert 'immobilien_patch' in tools['immobilien_update_status'].description
    assert 'immobilien_update_status' in tools['immobilien_patch'].description


def test_split_units_requires_unit_ids(tools):
    required = tools['immobilien_split_units'].parameters.get('required', [])
    assert {'immobilie_id', 'unit_ids'} <= set(required)
    assert 'target_type' not in required


def test_split_units_names_every_allowed_target_type(tools):
    description = tools['immobilien_split_units'].description
    missing = [code for code in PROPERTY_TYPE_CODES if code not in description]
    assert not missing, f'immobilien_split_units does not name {missing}'


def test_split_units_sends_unit_ids_and_target_type(tools, captured):
    tools['immobilien_split_units'].fn(immobilie_id='imm-1', unit_ids=['u-1', 'u-2'], target_type='EFH')

    [request] = captured
    assert request.method == 'POST'
    assert request.url.path == '/api/v2/immobilien/imm-1/split-units'
    assert json.loads(request.read()) == {'unit_ids': ['u-1', 'u-2'], 'target_type': 'EFH'}


def test_split_units_accepts_unit_ids_as_json_string(tools, captured):
    """Some MCP clients (ChatGPT) send arrays as JSON-encoded strings."""
    tools['immobilien_split_units'].fn(immobilie_id='imm-1', unit_ids='["u-1"]')

    [request] = captured
    assert json.loads(request.read()) == {'unit_ids': ['u-1']}


def test_split_units_rejects_a_single_id_instead_of_a_list(tools, captured):
    with pytest.raises(ValueError, match='unit_ids'):
        tools['immobilien_split_units'].fn(immobilie_id='imm-1', unit_ids='u-1')
    assert captured == []
