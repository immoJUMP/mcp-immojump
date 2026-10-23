import httpx
import pytest
import json

from mcp_immojump.client import ImmojumpAPIClient, ImmojumpCredentials


def test_credentials_allowlist_rejects_unknown_url():
    with pytest.raises(ValueError):
        ImmojumpCredentials(
            base_url='https://evil.example.com',
            token='abc',
            organisation_id='org-1',
        )


def test_credentials_require_token():
    with pytest.raises(ValueError):
        ImmojumpCredentials(
            base_url='http://localhost:8081',
            token='',
            organisation_id='org-1',
        )


def test_credentials_allow_empty_org_id():
    """organisation_id may be empty for user_me/organisation_list calls."""
    creds = ImmojumpCredentials(
        base_url='http://localhost:8081',
        token='abc',
        organisation_id='',
    )
    assert creds.token == 'abc'
    assert creds.organisation_id == ''


def test_contacts_import_preview_json_payload_contains_org_id():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured['path'] = request.url.path
        captured['json'] = request.read().decode('utf-8')
        return httpx.Response(200, json={'job_id': '1', 'status': 'completed'})

    transport = httpx.MockTransport(handler)
    creds = ImmojumpCredentials(
        base_url='http://localhost:8081',
        token='abc',
        organisation_id='org-1',
    )

    with ImmojumpAPIClient(creds, transport=transport) as client:
        payload = client.contacts_import_unified(
            source_type='csv',
            dry_run=True,
            source_text='a,b\n1,2',
        )

    assert payload['status'] == 'completed'
    assert captured['path'] == '/api/contacts/import-unified'
    request_payload = json.loads(captured['json'])
    assert request_payload['organisation_id'] == 'org-1'
    assert request_payload['dry_run'] is True


def test_pipeline_list_uses_org_path_and_header():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured['path'] = request.url.path
        captured['x_org'] = request.headers.get('X-Organisation-Id')
        return httpx.Response(200, json=[{'id': 1, 'name': 'Test'}])

    transport = httpx.MockTransport(handler)
    creds = ImmojumpCredentials(
        base_url='http://localhost:8081',
        token='abc',
        organisation_id='org-1',
    )

    with ImmojumpAPIClient(creds, transport=transport) as client:
        payload = client.pipeline_list()

    assert payload[0]['id'] == 1
    assert captured['path'] == '/api/pipelines/org-1/pipelines'
    assert captured['x_org'] == 'org-1'


def test_pipeline_import_yaml_sends_query_and_content_type():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured['path'] = request.url.path
        captured['query'] = dict(request.url.params)
        captured['content_type'] = request.headers.get('Content-Type')
        captured['body'] = request.read().decode('utf-8')
        return httpx.Response(200, json={'pipeline_id': 42})

    transport = httpx.MockTransport(handler)
    creds = ImmojumpCredentials(
        base_url='http://localhost:8081',
        token='abc',
        organisation_id='org-1',
    )

    with ImmojumpAPIClient(creds, transport=transport) as client:
        payload = client.pipeline_import(payload='pipeline:\n  name: Test')

    assert payload['pipeline_id'] == 42
    assert captured['path'] == '/api/pipelines/pipelines/import'
    assert captured['query']['organisation_id'] == 'org-1'
    assert captured['content_type'] == 'application/x-yaml'
    assert 'pipeline:' in captured['body']


def _read_only_403(request: httpx.Request) -> httpx.Response:
    return httpx.Response(403, json={
        'message': (
            'Dieser Zugangsschlüssel darf nur lesen. Zum Ändern lege unter Einstellungen → '
            'Schnittstellen-Zugang einen Zugang mit „Lesen und ändern" an.'
        ),
        'code': 'READ_ONLY_TOKEN',
    })


def test_read_only_token_error_tells_user_what_to_do():
    """A read-only key must not end in a bare 403 the model retries forever.

    The rendered error is what ChatGPT/Claude shows: it names the fix (new
    key with write access, reconnect the app) and tells the model to stop.
    """
    from mcp_immojump.client import ImmojumpAPIError

    creds = ImmojumpCredentials(
        base_url='http://localhost:8081', token='ijr_abc', organisation_id='org-1',
    )
    client = ImmojumpAPIClient(creds, transport=httpx.MockTransport(_read_only_403))
    with pytest.raises(ImmojumpAPIError) as exc:
        client._request('POST', '/api/immobilien', json={'name': 'X'})
    text = str(exc.value)
    assert 'Lesen und ändern' in text
    assert 'neu verbinden' in text
    assert 'nicht erneut' in text.lower()
