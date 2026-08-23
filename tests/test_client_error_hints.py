"""The backend hands out actionable hints on validation errors — the client
must not swallow them.

``modules/utils/validation_errors.py`` in the backend enriches every 400 with
``valid_values`` (allowed enum values), ``valid_fields`` and
``field_suggestions`` ("did you mean contact_ids?"). Those fields exist so an
agent can fix its own call on the next try. They only help if they survive the
trip through this client into the text the model actually sees.
"""

import httpx
import pytest

from mcp_immojump.client import ImmojumpAPIClient, ImmojumpAPIError, ImmojumpCredentials


def build_client(handler) -> ImmojumpAPIClient:
    creds = ImmojumpCredentials(
        base_url='http://localhost:8081',
        token='tok',
        organisation_id='org-1',
    )
    client = ImmojumpAPIClient(creds)
    client._client = httpx.Client(
        base_url='http://localhost:8081',
        transport=httpx.MockTransport(handler),
    )
    return client


VALIDATION_PAYLOAD = {
    'message': 'Validierungsfehler.',
    'errors': {
        'contact_id': ['Unknown field.'],
        'type': ['Invalid enum value task'],
    },
    'valid_values': {
        'type': ['ANRUF', 'BESICHTIGUNG', 'BRIEF', 'E-MAIL', 'MEETING', 'NOTIZ', 'SONSTIGES'],
    },
    'field_suggestions': {'contact_id': ['contact_ids']},
    'valid_fields': ['contact_ids', 'description', 'title', 'type'],
}


def test_validation_hints_reach_the_model():
    """The rendered exception text carries the field name, the suggestion and
    the allowed values — that is all a model needs to retry correctly."""
    client = build_client(lambda request: httpx.Response(400, json=VALIDATION_PAYLOAD))

    with pytest.raises(ImmojumpAPIError) as excinfo:
        client._request('POST', '/api/activities/activities', json={'type': 'task'})

    text = str(excinfo.value)
    assert 'Validierungsfehler.' in text
    assert 'contact_id' in text
    assert 'contact_ids' in text, 'the suggestion is the whole point'
    assert 'SONSTIGES' in text, 'allowed enum values must be visible'


def test_payload_stays_available_for_callers():
    """Tools may want to react programmatically instead of parsing prose."""
    client = build_client(lambda request: httpx.Response(400, json=VALIDATION_PAYLOAD))

    with pytest.raises(ImmojumpAPIError) as excinfo:
        client._request('POST', '/api/activities/activities', json={})

    error = excinfo.value
    assert error.status_code == 400
    assert error.payload['field_suggestions'] == {'contact_id': ['contact_ids']}
    assert error.message == 'Validierungsfehler.', 'the plain message must stay unchanged'


def test_error_key_variant_is_still_supported():
    """Contact routes answer with ``error`` (singular) instead of ``message``."""
    payload = {'error': {'email': ['Not a valid email address.']}, 'success': False}
    client = build_client(lambda request: httpx.Response(400, json=payload))

    with pytest.raises(ImmojumpAPIError) as excinfo:
        client._request('POST', '/api/contacts', json={'email': 'nope'})

    assert 'Not a valid email address.' in str(excinfo.value)


def test_plain_error_is_unchanged():
    """A response without hints must render exactly as before — no noise."""
    client = build_client(lambda request: httpx.Response(404, json={'message': 'Nicht gefunden.'}))

    with pytest.raises(ImmojumpAPIError) as excinfo:
        client._request('GET', '/api/contacts/does-not-exist')

    assert str(excinfo.value) == 'ImmoJUMP API error (404): Nicht gefunden.'


def test_non_json_error_body_still_works():
    client = build_client(lambda request: httpx.Response(502, text='<html>Bad Gateway</html>'))

    with pytest.raises(ImmojumpAPIError) as excinfo:
        client._request('GET', '/api/contacts')

    assert '502' in str(excinfo.value)
    assert excinfo.value.payload == {}


def test_truncated_hint_lists_stay_readable():
    """Long allowed-value lists must not bury the message."""
    payload = {
        'message': 'Validierungsfehler.',
        'errors': {'status': ['Invalid enum value x']},
        'valid_values': {'status': [f'Wert{i}' for i in range(40)]},
    }
    client = build_client(lambda request: httpx.Response(400, json=payload))

    with pytest.raises(ImmojumpAPIError) as excinfo:
        client._request('POST', '/api/activities/activities', json={})

    text = str(excinfo.value)
    assert 'Wert0' in text
    assert len(text) < 1000, 'the rendered error must stay compact'
