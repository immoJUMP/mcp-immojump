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
