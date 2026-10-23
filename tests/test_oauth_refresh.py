"""Refresh tokens and stateless OAuth artefacts.

ChatGPT's scheduled tasks run without a user at the keyboard. Before this,
``/oauth/token`` announced ``expires_in`` 24 h but offered no refresh grant,
so after a day ChatGPT could only ask the user to log in again — and an
unattended run failed with "Zugriff verweigert / Token abgelaufen".

Codes and client registrations lived in process memory, so every rollout
(and the second pod during a rolling update) forgot them mid-flow.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import time
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from mcp_immojump import oauth
from mcp_immojump.oauth import create_oauth_routes, decode_access_token
from mcp_immojump.servers._base import _OAuthFrontMiddleware

REDIRECT = 'https://chatgpt.com/connector_platform_oauth_redirect'
API_TOKEN = 'ijw_' + 'x' * 43
ORG_ID = '7f3c2a10-0000-4000-8000-000000000001'


@pytest.fixture()
def secret(monkeypatch):
    monkeypatch.setenv('IMMOJUMP_MCP_OAUTH_SECRET', 'test-secret-' + 'a' * 40)
    monkeypatch.setenv('IMMOJUMP_BASE_URL', 'http://127.0.0.1:1')  # unreachable
    oauth._reset_keys_for_tests()
    yield
    oauth._reset_keys_for_tests()


@pytest.fixture()
def no_secret(monkeypatch):
    monkeypatch.delenv('IMMOJUMP_MCP_OAUTH_SECRET', raising=False)
    monkeypatch.setenv('IMMOJUMP_BASE_URL', 'http://127.0.0.1:1')
    oauth._reset_keys_for_tests()
    yield
    oauth._reset_keys_for_tests()


def _client() -> TestClient:
    return TestClient(Starlette(routes=create_oauth_routes()), base_url='https://mcp.immojump.de')


def _pkce_pair():
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode('ascii')).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')


def _authorize(client: TestClient, challenge: str, client_id: str = 'chatgpt', **extra) -> str:
    resp = client.post('/oauth/authorize', data={
        'api_token': API_TOKEN,
        'org_id': ORG_ID,
        'redirect_uri': REDIRECT,
        'state': 's',
        'code_challenge': challenge,
        'client_id': client_id,
        **extra,
    }, follow_redirects=False)
    assert resp.status_code == 302, resp.text
    return parse_qs(urlparse(resp.headers['location']).query)['code'][0]


def _login(client: TestClient) -> dict:
    verifier, challenge = _pkce_pair()
    code = _authorize(client, challenge)
    resp = client.post('/oauth/token', data={
        'grant_type': 'authorization_code', 'code': code,
        'code_verifier': verifier, 'redirect_uri': REDIRECT,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Refresh grant
# ---------------------------------------------------------------------------

class TestRefreshGrant:
    def test_code_exchange_returns_refresh_token(self, secret):
        data = _login(_client())
        assert data['refresh_token']
        assert data['expires_in'] > 0
        assert decode_access_token(data['access_token']) == (API_TOKEN, ORG_ID)

    def test_refresh_issues_new_working_access_token(self, secret):
        client = _client()
        first = _login(client)
        resp = client.post('/oauth/token', data={
            'grant_type': 'refresh_token', 'refresh_token': first['refresh_token'],
        })
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert decode_access_token(data['access_token']) == (API_TOKEN, ORG_ID)
        assert data['token_type'] == 'bearer'
        # Rotation: the client always gets a fresh refresh token to store.
        assert data['refresh_token']

    def test_refresh_works_on_another_pod_after_restart(self, secret):
        """No server-side state: a fresh process with the same secret accepts it."""
        first = _login(_client())
        oauth._reset_keys_for_tests()  # simulates a new pod / restart
        resp = _client().post('/oauth/token', json={
            'grant_type': 'refresh_token', 'refresh_token': first['refresh_token'],
        })
        assert resp.status_code == 200, resp.text

    def test_access_token_is_not_accepted_as_refresh_token(self, secret):
        first = _login(_client())
        resp = _client().post('/oauth/token', data={
            'grant_type': 'refresh_token', 'refresh_token': first['access_token'],
        })
        assert resp.status_code == 400
        assert resp.json()['error'] == 'invalid_grant'

    def test_tampered_refresh_token_is_rejected(self, secret):
        first = _login(_client())
        token = first['refresh_token']
        tampered = token[:-6] + ('A' if token[-6] != 'A' else 'B') + token[-5:]
        resp = _client().post('/oauth/token', data={
            'grant_type': 'refresh_token', 'refresh_token': tampered,
        })
        assert resp.status_code == 400
        assert resp.json()['error'] == 'invalid_grant'

    def test_refresh_token_from_other_secret_is_rejected(self, secret, monkeypatch):
        first = _login(_client())
        monkeypatch.setenv('IMMOJUMP_MCP_OAUTH_SECRET', 'other-secret-' + 'b' * 40)
        oauth._reset_keys_for_tests()
        resp = _client().post('/oauth/token', data={
            'grant_type': 'refresh_token', 'refresh_token': first['refresh_token'],
        })
        assert resp.status_code == 400

    def test_rotated_secret_still_reads_old_tokens(self, secret, monkeypatch):
        """Comma-separated secrets: first one signs, all of them verify."""
        first = _login(_client())
        old = 'test-secret-' + 'a' * 40
        monkeypatch.setenv('IMMOJUMP_MCP_OAUTH_SECRET', f'new-secret-{"c" * 40},{old}')
        oauth._reset_keys_for_tests()
        resp = _client().post('/oauth/token', data={
            'grant_type': 'refresh_token', 'refresh_token': first['refresh_token'],
        })
        assert resp.status_code == 200

    def test_refresh_token_bound_to_client(self, secret):
        first = _login(_client())
        resp = _client().post('/oauth/token', data={
            'grant_type': 'refresh_token', 'refresh_token': first['refresh_token'],
            'client_id': 'someone-else',
        })
        assert resp.status_code == 400
        assert resp.json()['error'] == 'invalid_grant'

    def test_expired_refresh_token_is_rejected(self, secret, monkeypatch):
        first = _login(_client())
        real_time = time.time
        monkeypatch.setattr(oauth.time, 'time', lambda: real_time() + oauth._REFRESH_TTL + 120)
        resp = _client().post('/oauth/token', data={
            'grant_type': 'refresh_token', 'refresh_token': first['refresh_token'],
        })
        assert resp.status_code == 400

    def test_refresh_rejected_when_backend_revoked_api_token(self, secret, monkeypatch):
        """Deleting the access key in immoJUMP must end the ChatGPT connection."""
        first = _login(_client())

        def fake_get(*args, **kwargs):
            return httpx.Response(401, json={'message': 'ungültig', 'code': 'INVALID_TOKEN'})

        monkeypatch.setattr(oauth.httpx, 'get', fake_get)
        resp = _client().post('/oauth/token', data={
            'grant_type': 'refresh_token', 'refresh_token': first['refresh_token'],
        })
        assert resp.status_code == 400
        assert resp.json()['error'] == 'invalid_grant'

    def test_refresh_token_does_not_contain_api_token_in_clear(self, secret):
        data = _login(_client())
        for value in (data['refresh_token'], data['access_token']):
            assert API_TOKEN not in value
            padded = value + '=' * (-len(value) % 4)
            for candidate in (value, padded, value.split('.', 1)[-1]):
                try:
                    decoded = base64.urlsafe_b64decode(candidate + '=' * (-len(candidate) % 4))
                except Exception:
                    continue
                assert API_TOKEN.encode() not in decoded

    def test_missing_refresh_token_param(self, secret):
        resp = _client().post('/oauth/token', data={'grant_type': 'refresh_token'})
        assert resp.status_code == 400
        assert resp.json()['error'] == 'invalid_request'


class TestDiscoveryAdvertisesRefresh:
    def test_metadata_lists_refresh_grant(self, secret):
        data = _client().get('/.well-known/oauth-authorization-server').json()
        assert data['grant_types_supported'] == ['authorization_code', 'refresh_token']

    def test_registration_lists_refresh_grant(self, secret):
        resp = _client().post('/oauth/register', json={'redirect_uris': [REDIRECT]})
        assert resp.json()['grant_types'] == ['authorization_code', 'refresh_token']


# ---------------------------------------------------------------------------
# Without a configured secret: exactly the old behaviour, loudly logged
# ---------------------------------------------------------------------------

class TestWithoutSecret:
    def test_no_refresh_token_and_legacy_access_token(self, no_secret, caplog):
        with caplog.at_level('ERROR', logger='mcp_immojump.oauth'):
            data = _login(_client())
        assert 'refresh_token' not in data
        expected = base64.urlsafe_b64encode(f'{API_TOKEN}:{ORG_ID}'.encode()).decode()
        assert data['access_token'] == expected
        assert 'IMMOJUMP_MCP_OAUTH_SECRET' in caplog.text

    def test_metadata_does_not_promise_refresh(self, no_secret):
        data = _client().get('/.well-known/oauth-authorization-server').json()
        assert data['grant_types_supported'] == ['authorization_code']

    def test_refresh_grant_unsupported(self, no_secret):
        resp = _client().post('/oauth/token', data={
            'grant_type': 'refresh_token', 'refresh_token': 'whatever',
        })
        assert resp.status_code == 400
        assert resp.json()['error'] == 'unsupported_grant_type'


class TestLegacyTokensKeepWorking:
    def test_old_base64_access_token_still_decodes(self, secret):
        """Existing ChatGPT connections hold base64 tokens — must not break."""
        legacy = base64.urlsafe_b64encode(f'{API_TOKEN}:{ORG_ID}'.encode()).decode()
        assert decode_access_token(legacy) == (API_TOKEN, ORG_ID)


# ---------------------------------------------------------------------------
# Stateless codes and client registrations
# ---------------------------------------------------------------------------

class TestStatelessFlow:
    def test_code_survives_restart(self, secret):
        """Code issued by pod A, exchanged at pod B (rolling update)."""
        verifier, challenge = _pkce_pair()
        code = _authorize(_client(), challenge)
        oauth._reset_keys_for_tests()
        resp = _client().post('/oauth/token', data={
            'grant_type': 'authorization_code', 'code': code,
            'code_verifier': verifier, 'redirect_uri': REDIRECT,
        })
        assert resp.status_code == 200, resp.text

    def test_code_does_not_contain_api_token_in_clear(self, secret):
        _, challenge = _pkce_pair()
        code = _authorize(_client(), challenge)
        assert API_TOKEN not in code

    def test_code_expires(self, secret, monkeypatch):
        verifier, challenge = _pkce_pair()
        code = _authorize(_client(), challenge)
        real_time = time.time
        monkeypatch.setattr(oauth.time, 'time', lambda: real_time() + oauth._CODE_TTL + 120)
        resp = _client().post('/oauth/token', data={
            'grant_type': 'authorization_code', 'code': code, 'code_verifier': verifier,
        })
        assert resp.status_code == 400

    def test_registered_client_survives_restart(self, secret):
        """redirect_uri check must still apply after the pod that registered is gone."""
        client_id = _client().post(
            '/oauth/register', json={'redirect_uris': [REDIRECT]},
        ).json()['client_id']
        oauth._reset_keys_for_tests()
        resp = _client().post('/oauth/authorize', data={
            'api_token': API_TOKEN, 'org_id': ORG_ID,
            'redirect_uri': 'https://evil.example.com/cb',
            'client_id': client_id,
        }, follow_redirects=False)
        assert resp.status_code == 400

    def test_registered_client_with_matching_redirect_passes(self, secret):
        client_id = _client().post(
            '/oauth/register', json={'redirect_uris': [REDIRECT]},
        ).json()['client_id']
        _, challenge = _pkce_pair()
        assert _authorize(_client(), challenge, client_id=client_id)


# ---------------------------------------------------------------------------
# Middleware: expired sealed token → 401 so the client refreshes
# ---------------------------------------------------------------------------

def _mcp_stack() -> TestClient:
    async def mcp_route(request):
        return PlainTextResponse('mcp-body')

    app = Starlette(routes=[Route('/mcp', mcp_route, methods=['GET', 'POST'])])
    return TestClient(_OAuthFrontMiddleware(app))


class TestMiddlewareSignalsExpiry:
    def test_valid_sealed_token_passes(self, secret):
        data = _login(_client())
        resp = _mcp_stack().post('/mcp', headers={'Authorization': f'Bearer {data["access_token"]}'})
        assert resp.status_code == 200

    def test_expired_sealed_token_gets_401_invalid_token(self, secret, monkeypatch):
        data = _login(_client())
        real_time = time.time
        monkeypatch.setattr(oauth.time, 'time', lambda: real_time() + oauth._ACCESS_TTL + 120)
        resp = _mcp_stack().post('/mcp', headers={'Authorization': f'Bearer {data["access_token"]}'})
        assert resp.status_code == 401
        challenge = resp.headers['www-authenticate']
        assert 'error="invalid_token"' in challenge
        assert 'resource_metadata=' in challenge

    def test_plain_api_token_with_org_header_untouched(self, secret):
        resp = _mcp_stack().post('/mcp', headers={
            'Authorization': f'Bearer {API_TOKEN}', 'X-Organisation-Id': ORG_ID,
        })
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Authorize page: write access must be obvious
# ---------------------------------------------------------------------------

class TestAuthorizePageExplainsWriteAccess:
    def test_form_says_write_access_is_needed_for_changes(self, secret):
        resp = _client().get('/oauth/authorize', params={'redirect_uri': REDIRECT})
        assert resp.status_code == 200
        assert 'Lesen und ändern' in resp.text
        assert 'Schnittstellen-Zugang' in resp.text

    def test_form_names_where_the_user_goes_back_to(self, secret):
        resp = _client().get('/oauth/authorize', params={'redirect_uri': REDIRECT})
        assert 'chatgpt.com' in resp.text

    def test_read_only_token_gets_warning_instead_of_silent_connect(self, secret):
        resp = _client().post('/oauth/authorize', data={
            'api_token': 'ijr_' + 'y' * 43, 'org_id': ORG_ID, 'redirect_uri': REDIRECT,
        }, follow_redirects=False)
        assert resp.status_code == 200
        assert 'nur lesen' in resp.text
        assert 'confirm_read_only' in resp.text
        assert resp.headers['cache-control'] == 'no-store'

    def test_read_only_token_connects_after_confirmation(self, secret):
        resp = _client().post('/oauth/authorize', data={
            'api_token': 'ijr_' + 'y' * 43, 'org_id': ORG_ID, 'redirect_uri': REDIRECT,
            'confirm_read_only': '1',
        }, follow_redirects=False)
        assert resp.status_code == 302
