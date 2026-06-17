"""Verify the MCP client normalizes friendly aliases into the actual
ActivitySchema field names before POSTing to the backend.

These aliases are advertised in tools/activities.py docstrings (so the
LLM/customer will use them), and the strict marshmallow schema would
otherwise 400 with 'Unknown field' for any of them.
"""
from unittest.mock import patch

from mcp_immojump.client import ImmojumpAPIClient, ImmojumpCredentials


def _client():
    creds = ImmojumpCredentials(
        base_url='https://immojump.de',
        token='tok',
        organisation_id='org-1',
    )
    return ImmojumpAPIClient(creds)


def _captured_post(monkeypatched_request):
    posts = [c for c in monkeypatched_request.call_args_list if c.args[0] == 'POST']
    assert posts, 'no POST captured'
    return posts[0]


def test_activities_create_renames_activity_status_to_status():
    client = _client()
    with patch.object(client, '_request', return_value={}) as m:
        client.activities_create(data={
            'title': 'KI-Recherche', 'type': 'NOTIZ',
            'activity_status': 'Geplant', 'priority': 'NA',
            'contact_ids': ['c-1'],
        })
    posted = m.call_args.kwargs['json']
    assert 'activity_status' not in posted
    assert posted['status'] == 'Geplant'


def test_activities_create_maps_due_date_to_scheduled_end():
    client = _client()
    with patch.object(client, '_request', return_value={}) as m:
        client.activities_create(data={
            'title': 'X', 'type': 'NOTIZ',
            'activity_status': 'Geplant', 'priority': 'NA',
            'due_date': '2026-06-16T16:45:00+00:00',
            'contact_ids': ['c-1'],
        })
    posted = m.call_args.kwargs['json']
    assert 'due_date' not in posted
    assert posted['scheduled_end'] == '2026-06-16T16:45:00+00:00'


def test_activities_create_singular_contact_id_to_list():
    client = _client()
    with patch.object(client, '_request', return_value={}) as m:
        client.activities_create(data={
            'title': 'X', 'type': 'NOTIZ',
            'activity_status': 'Geplant', 'priority': 'NA',
            'contact_id': 'c-7',
        })
    posted = m.call_args.kwargs['json']
    assert 'contact_id' not in posted
    assert posted['contact_ids'] == ['c-7']


def test_activities_create_does_not_overwrite_existing_real_field():
    client = _client()
    with patch.object(client, '_request', return_value={}) as m:
        client.activities_create(data={
            'title': 'X', 'type': 'NOTIZ',
            'status': 'Abgeschlossen',
            'activity_status': 'Geplant',  # alias should NOT win when real field is set
            'priority': 'NA',
            'contact_ids': ['c-1'],
        })
    posted = m.call_args.kwargs['json']
    assert posted['status'] == 'Abgeschlossen'
    assert 'activity_status' not in posted


def test_activities_update_also_normalizes():
    client = _client()
    with patch.object(client, '_request', return_value={}) as m:
        client.activities_update(activity_id='a-1', data={
            'activity_status': 'Abgeschlossen',
            'due_date': '2026-06-16',
            'contact_id': 'c-9',
        })
    posted = m.call_args.kwargs['json']
    assert posted['status'] == 'Abgeschlossen'
    assert 'due_date' not in posted
    assert posted['scheduled_end'] == '2026-06-16T00:00:00+00:00'  # _normalize_payload_dates expanded it
    assert posted['contact_ids'] == ['c-9']
