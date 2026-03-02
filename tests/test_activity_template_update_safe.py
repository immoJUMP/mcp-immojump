import json

import httpx
import pytest

from mcp_immojump.client import ImmojumpAPIClient, ImmojumpAPIError, ImmojumpCredentials


def _base_template() -> dict:
    return {
        'id': 'tmpl-1',
        'title': 'Alt',
        'description': 'Alt Beschreibung',
        'updated_at': '2026-03-02T10:00:00+00:00',
        'organisation_id': 'org-1',
        'status_id': 10,
        'outcomes': [
            {
                'id': 'out-1',
                'key': 'absage',
                'label': 'Absage',
                'description': None,
                'order': 0,
                'actions': [
                    {
                        'type': 'STATUS_CHANGE',
                        'target_status_id': 10,
                        'target_status_name': 'Archiv',
                    }
                ],
            },
            {
                'id': 'out-2',
                'key': 'wiedervorlage',
                'label': 'Wiedervorlage',
                'description': None,
                'order': 1,
                'actions': [],
            },
        ],
    }


def _client_with(handler) -> ImmojumpAPIClient:
    transport = httpx.MockTransport(handler)
    creds = ImmojumpCredentials(
        base_url='http://localhost:8081',
        token='abc',
        organisation_id='org-1',
    )
    return ImmojumpAPIClient(creds, transport=transport)


def _json_body(request: httpx.Request) -> dict:
    body = request.read().decode('utf-8')
    return json.loads(body or '{}')


def test_activity_template_update_title_description_keeps_outcomes_untouched():
    template = _base_template()
    captured_put = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == 'GET' and request.url.path.endswith('/activity_templates/tmpl-1'):
            return httpx.Response(200, json=template)
        if request.method == 'PUT' and request.url.path.endswith('/activity_templates/tmpl-1'):
            captured_put['payload'] = _json_body(request)
            response_payload = dict(template)
            response_payload.update(captured_put['payload'])
            return httpx.Response(200, json=response_payload)
        raise AssertionError(f'unexpected request: {request.method} {request.url.path}')

    with _client_with(handler) as client:
        response = client.activity_template_update(
            template_id='tmpl-1',
            data={'title': 'Neu', 'description': 'Neu Beschreibung'},
        )

    assert response['title'] == 'Neu'
    assert response['description'] == 'Neu Beschreibung'
    assert 'outcomes' not in captured_put['payload']


def test_activity_template_update_merges_single_outcome_without_touching_others():
    template = _base_template()
    captured_put = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == 'GET' and request.url.path.endswith('/activity_templates/tmpl-1'):
            return httpx.Response(200, json=template)
        if request.method == 'GET' and request.url.path.endswith('/statuses/statuses'):
            return httpx.Response(
                200,
                json=[{'id': 10, 'name': 'Archiv', 'pipeline': {'organisation_id': 'org-1'}}],
            )
        if request.method == 'PUT' and request.url.path.endswith('/activity_templates/tmpl-1'):
            captured_put['payload'] = _json_body(request)
            return httpx.Response(200, json=captured_put['payload'])
        raise AssertionError(f'unexpected request: {request.method} {request.url.path}')

    with _client_with(handler) as client:
        client.activity_template_update(
            template_id='tmpl-1',
            data={
                'outcomes': [
                    {'id': 'out-1', 'label': 'Absage aktualisiert'},
                ]
            },
        )

    merged_outcomes = captured_put['payload']['outcomes']
    assert len(merged_outcomes) == 2
    out1 = next(item for item in merged_outcomes if item['id'] == 'out-1')
    out2 = next(item for item in merged_outcomes if item['id'] == 'out-2')
    assert out1['label'] == 'Absage aktualisiert'
    assert out1['actions'][0]['target_status_name'] == 'Archiv'
    assert out2['label'] == 'Wiedervorlage'


def test_activity_template_update_replace_outcomes_true_replaces_fully():
    template = _base_template()
    captured_put = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == 'GET' and request.url.path.endswith('/activity_templates/tmpl-1'):
            return httpx.Response(200, json=template)
        if request.method == 'PUT' and request.url.path.endswith('/activity_templates/tmpl-1'):
            captured_put['payload'] = _json_body(request)
            return httpx.Response(200, json=captured_put['payload'])
        raise AssertionError(f'unexpected request: {request.method} {request.url.path}')

    with _client_with(handler) as client:
        client.activity_template_update(
            template_id='tmpl-1',
            data={
                'replace_outcomes': True,
                'outcomes': [
                    {
                        'id': 'out-new',
                        'key': 'neu',
                        'label': 'Neu',
                        'actions': [],
                    }
                ],
            },
        )

    assert captured_put['payload']['outcomes'] == [
        {
            'id': 'out-new',
            'key': 'neu',
            'label': 'Neu',
            'actions': [],
        }
    ]


def test_activity_template_update_if_updated_at_conflict_returns_409():
    template = _base_template()
    seen_methods = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_methods.append(request.method)
        if request.method == 'GET' and request.url.path.endswith('/activity_templates/tmpl-1'):
            return httpx.Response(200, json=template)
        raise AssertionError(f'unexpected request: {request.method} {request.url.path}')

    with _client_with(handler) as client:
        with pytest.raises(ImmojumpAPIError) as exc:
            client.activity_template_update(
                template_id='tmpl-1',
                data={
                    'if_updated_at': '2026-03-02T09:59:00+00:00',
                    'title': 'Neu',
                },
            )

    assert exc.value.status_code == 409
    assert seen_methods == ['GET']


def test_activity_template_update_rejects_status_name_mismatch():
    template = _base_template()
    seen_put = {'called': False}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == 'GET' and request.url.path.endswith('/activity_templates/tmpl-1'):
            return httpx.Response(200, json=template)
        if request.method == 'GET' and request.url.path.endswith('/statuses/statuses'):
            return httpx.Response(
                200,
                json=[{'id': 10, 'name': 'Archiv', 'pipeline': {'organisation_id': 'org-1'}}],
            )
        if request.method == 'PUT':
            seen_put['called'] = True
            return httpx.Response(200, json={})
        raise AssertionError(f'unexpected request: {request.method} {request.url.path}')

    with _client_with(handler) as client:
        with pytest.raises(ImmojumpAPIError) as exc:
            client.activity_template_update(
                template_id='tmpl-1',
                data={
                    'outcomes': [
                        {
                            'id': 'out-1',
                            'actions': [
                                {
                                    'type': 'STATUS_CHANGE',
                                    'target_status_id': 10,
                                    'target_status_name': 'Wiedervorlage',
                                }
                            ],
                        }
                    ]
                },
            )

    assert exc.value.status_code == 400
    assert seen_put['called'] is False


def test_activity_template_update_rejects_invalid_create_activity_template_id():
    template = _base_template()
    seen_put = {'called': False}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == 'GET' and request.url.path.endswith('/activity_templates/tmpl-1'):
            return httpx.Response(200, json=template)
        if request.method == 'GET' and request.url.path.endswith('/activity_templates/tmpl-404'):
            return httpx.Response(404, json={'error': 'Template not found'})
        if request.method == 'PUT':
            seen_put['called'] = True
            return httpx.Response(200, json={})
        raise AssertionError(f'unexpected request: {request.method} {request.url.path}')

    with _client_with(handler) as client:
        with pytest.raises(ImmojumpAPIError) as exc:
            client.activity_template_update(
                template_id='tmpl-1',
                data={
                    'outcomes': [
                        {
                            'id': 'out-1',
                            'actions': [{'type': 'CREATE_ACTIVITY', 'template_id': 'tmpl-404'}],
                        }
                    ]
                },
            )

    assert exc.value.status_code == 404
    assert seen_put['called'] is False


def test_activity_template_update_dry_run_returns_diff_and_does_not_persist():
    template = _base_template()
    seen_put = {'called': False}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == 'GET' and request.url.path.endswith('/activity_templates/tmpl-1'):
            return httpx.Response(200, json=template)
        if request.method == 'GET' and request.url.path.endswith('/statuses/statuses'):
            return httpx.Response(
                200,
                json=[{'id': 10, 'name': 'Archiv', 'pipeline': {'organisation_id': 'org-1'}}],
            )
        if request.method == 'PUT':
            seen_put['called'] = True
            return httpx.Response(200, json={})
        raise AssertionError(f'unexpected request: {request.method} {request.url.path}')

    with _client_with(handler) as client:
        preview = client.activity_template_update(
            template_id='tmpl-1',
            data={
                'dry_run': True,
                'title': 'Neu',
                'outcomes': [{'id': 'out-2', 'label': 'Wiedervorlage morgen'}],
            },
        )

    assert preview['dry_run'] is True
    assert preview['has_changes'] is True
    assert 'title' in preview['changed_fields']
    assert 'outcomes' in preview['changed_fields']
    assert seen_put['called'] is False
