"""Where /oauth/authorize may send a code, and PKCE as a must.

Registration is open (DCR without authentication, client_id metadata documents
are not fetched), so a client_id says nothing about who asks. Before this, any
redirect_uri was accepted unless the client_id was one we had sealed — and a
sealed one could be obtained with any redirect_uri. A link to the real login
page could therefore send the code for the entered access key anywhere.

Now the redirect host itself must be trusted: the AI apps we serve, loopback
for desktop/CLI clients, plus ``IMMOJUMP_MCP_OAUTH_REDIRECT_ORIGINS``.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from urllib.parse import parse_qs, urlparse

import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

from mcp_immojump import oauth
from mcp_immojump.oauth import create_oauth_routes

API_TOKEN = 'ijw_' + 'x' * 43
ORG_ID = '7f3c2a10-0000-4000-8000-000000000001'

# Seen in the access log of the hosted server (four weeks, 10/2026) or
# documented by the client vendor.
ALLOWED = [
    'https://chatgpt.com/connector/oauth/AbC-123_xyz',
    'https://chatgpt.com/connector_platform_oauth_redirect',
    'https://chat.openai.com/aip/g-123/oauth/callback',
    'https://claude.ai/api/mcp/auth_callback',
    'https://claude.com/api/mcp/auth_callback',
    'http://127.0.0.1:55352/callback/Q1w2E3r4T5y6',   # Codex CLI
    'http://localhost:3118/callback',                 # Claude Code
    'http://localhost/callback',
    'http://[::1]:8080/callback',
    'http://localhost:8787/callback',                 # Cursor (new)
    'cursor://anysphere.cursor-mcp/oauth/callback',   # Cursor (old)
    'https://www.cursor.com/agents/mcp/oauth/callback',
]

REJECTED = [
    'https://evil.example/cb',
    'https://chatgpt.com.evil.example/cb',
    'https://evil.example/chatgpt.com',
    'https://chatgpt.com@evil.example/cb',
    'https://evilchatgpt.com/cb',
    'https://sub.claude.ai.evil.example/cb',
    'http://chatgpt.com/connector/oauth/x',          # no TLS outside loopback
    'http://localhost.evil.example/cb',
    'http://127.0.0.1.evil.example/cb',
    'https://claude.ai/api/mcp/auth_callback#frag',
    'cursor://evil/cb',
    'javascript:alert(1)',
    'data:text/html,hi',
    '/relative/callback',
    'ftp://localhost/cb',
]


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv('IMMOJUMP_MCP_OAUTH_SECRET', 'test-secret-' + 'a' * 40)
    monkeypatch.setenv('IMMOJUMP_BASE_URL', 'http://127.0.0.1:1')  # unreachable
    monkeypatch.delenv('IMMOJUMP_MCP_OAUTH_REDIRECT_ORIGINS', raising=False)
    oauth._reset_keys_for_tests()
    yield
    oauth._reset_keys_for_tests()


def _client() -> TestClient:
    return TestClient(Starlette(routes=create_oauth_routes()), base_url='https://mcp.immojump.de')


def _pkce_pair():
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode('ascii')).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')


def _get(redirect_uri: str, client_id: str = 'whatever', **extra):
    _, challenge = _pkce_pair()
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'state': 's',
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
        **extra,
    }
    return _client().get('/oauth/authorize', params=params)


def _post(redirect_uri: str, client_id: str = 'whatever', **extra):
    _, challenge = _pkce_pair()
    data = {
        'api_token': API_TOKEN,
        'org_id': ORG_ID,
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'state': 's',
        'code_challenge': challenge,
        **extra,
    }
    return _client().post('/oauth/authorize', data=data, follow_redirects=False)


# ---------------------------------------------------------------------------
# Redirect allowlist on /oauth/authorize
# ---------------------------------------------------------------------------

class TestRedirectAllowlist:
    @pytest.mark.parametrize('redirect_uri', ALLOWED)
    def test_known_clients_see_the_login_form(self, redirect_uri):
        resp = _get(redirect_uri)
        assert resp.status_code == 200, resp.text
        assert 'name="api_token"' in resp.text

    @pytest.mark.parametrize('redirect_uri', ALLOWED)
    def test_known_clients_get_a_code(self, redirect_uri):
        resp = _post(redirect_uri)
        assert resp.status_code == 302, resp.text
        assert resp.headers['location'].startswith(redirect_uri)

    @pytest.mark.parametrize('redirect_uri', REJECTED)
    def test_untrusted_redirect_gets_no_login_form(self, redirect_uri):
        resp = _get(redirect_uri)
        assert resp.status_code == 400
        assert 'name="api_token"' not in resp.text

    @pytest.mark.parametrize('redirect_uri', REJECTED)
    def test_untrusted_redirect_gets_no_code(self, redirect_uri):
        resp = _post(redirect_uri)
        assert resp.status_code == 400
        assert 'location' not in resp.headers

    def test_rejection_names_the_host_without_echoing_markup(self):
        resp = _get('https://evil.example/<b>cb</b>')
        assert 'evil.example' in resp.text
        assert '<b>' not in resp.text

    def test_metadata_document_client_id_does_not_unlock_any_host(self):
        """client_id URLs are not fetched, so they cannot vouch for a redirect."""
        resp = _post('https://evil.example/cb', client_id='https://evil.example/client.json')
        assert resp.status_code == 400

    def test_lookalike_of_a_real_metadata_client_id_is_still_checked(self):
        resp = _post(
            'https://evil.example/cb',
            client_id='https://chatgpt.com/oauth/AbC-123_xyz/client.json',
        )
        assert resp.status_code == 400

    def test_sealed_registration_from_before_cannot_whitelist_a_host(self):
        """Registrations sealed by older versions accepted any redirect_uri."""
        client_id = oauth._seal('client', {'ru': ['https://evil.example/cb']})
        assert _get('https://evil.example/cb', client_id=client_id).status_code == 400
        assert _post('https://evil.example/cb', client_id=client_id).status_code == 400

    def test_sealed_registration_still_pins_the_exact_uri(self):
        client_id = oauth._seal('client', {'ru': ['http://localhost:3000/callback']})
        assert _post('http://localhost:4000/other', client_id=client_id).status_code == 400
        assert _post('http://localhost:3000/callback', client_id=client_id).status_code == 302

    def test_host_comparison_ignores_case(self):
        assert _post('https://ChatGPT.com/connector/oauth/x').status_code == 302


class TestRedirectOriginsFromEnv:
    def test_extra_origin_is_allowed(self, monkeypatch):
        monkeypatch.setenv(
            'IMMOJUMP_MCP_OAUTH_REDIRECT_ORIGINS',
            ' https://n8n.example.com , https://other.example:8443/ ',
        )
        assert _post('https://n8n.example.com/rest/oauth2-credential/callback').status_code == 302
        assert _post('https://other.example:8443/cb').status_code == 302

    def test_extra_origin_matches_port_exactly(self, monkeypatch):
        monkeypatch.setenv('IMMOJUMP_MCP_OAUTH_REDIRECT_ORIGINS', 'https://other.example:8443')
        assert _post('https://other.example/cb').status_code == 400
        assert _post('https://other.example:9443/cb').status_code == 400

    def test_extra_origin_does_not_open_subdomains(self, monkeypatch):
        monkeypatch.setenv('IMMOJUMP_MCP_OAUTH_REDIRECT_ORIGINS', 'https://n8n.example.com')
        assert _post('https://evil.n8n.example.com/cb').status_code == 400

    def test_defaults_stay_when_env_is_set(self, monkeypatch):
        monkeypatch.setenv('IMMOJUMP_MCP_OAUTH_REDIRECT_ORIGINS', 'https://n8n.example.com')
        assert _post('https://claude.ai/api/mcp/auth_callback').status_code == 302


# ---------------------------------------------------------------------------
# Registration only keeps trusted redirect_uris
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_untrusted_redirect_uris_are_dropped(self):
        resp = _client().post('/oauth/register', json={'redirect_uris': [
            'cursor://anysphere.cursor-mcp/oauth/callback',
            'https://evil.example/cb',
            'http://localhost:8787/callback',
        ]})
        assert resp.status_code == 201
        assert resp.json()['redirect_uris'] == [
            'cursor://anysphere.cursor-mcp/oauth/callback',
            'http://localhost:8787/callback',
        ]

    def test_only_untrusted_redirect_uris_is_rejected(self):
        resp = _client().post('/oauth/register', json={
            'redirect_uris': ['https://evil.example/cb'],
        })
        assert resp.status_code == 400
        assert resp.json()['error'] == 'invalid_redirect_uri'

    def test_registered_client_cannot_use_dropped_uri(self):
        client_id = _client().post('/oauth/register', json={'redirect_uris': [
            'https://evil.example/cb', 'http://localhost:8787/callback',
        ]}).json()['client_id']
        assert _post('https://evil.example/cb', client_id=client_id).status_code == 400
        assert _post('http://localhost:8787/callback', client_id=client_id).status_code == 302


# ---------------------------------------------------------------------------
# PKCE S256 is required
# ---------------------------------------------------------------------------

class TestPkceRequired:
    def test_get_without_code_challenge_is_rejected(self):
        resp = _client().get('/oauth/authorize', params={
            'client_id': 'x', 'redirect_uri': 'https://claude.ai/api/mcp/auth_callback',
        })
        assert resp.status_code == 400
        assert 'name="api_token"' not in resp.text

    def test_get_without_method_is_rejected(self):
        resp = _client().get('/oauth/authorize', params={
            'client_id': 'x', 'redirect_uri': 'https://claude.ai/api/mcp/auth_callback',
            'code_challenge': 'abc',
        })
        assert resp.status_code == 400

    def test_get_with_plain_is_rejected(self):
        resp = _get('https://claude.ai/api/mcp/auth_callback', code_challenge_method='plain')
        assert resp.status_code == 400

    def test_post_without_code_challenge_issues_no_code(self):
        resp = _post('https://claude.ai/api/mcp/auth_callback', code_challenge='')
        assert resp.status_code == 400
        assert 'location' not in resp.headers

    def test_post_with_plain_method_issues_no_code(self):
        resp = _post('https://claude.ai/api/mcp/auth_callback', code_challenge_method='plain')
        assert resp.status_code == 400

    def test_code_without_challenge_cannot_be_redeemed(self):
        """Codes minted before this version (or forged) carry no challenge."""
        code = oauth._seal('code', {
            't': API_TOKEN, 'o': ORG_ID, 'cc': '',
            'ru': 'https://claude.ai/api/mcp/auth_callback', 'cid': 'x',
        })
        resp = _client().post('/oauth/token', data={
            'grant_type': 'authorization_code', 'code': code,
        })
        assert resp.status_code == 400
        assert resp.json()['error'] == 'invalid_grant'

    def test_full_flow_with_s256(self):
        verifier, challenge = _pkce_pair()
        resp = _post('https://claude.ai/api/mcp/auth_callback', code_challenge=challenge)
        code = parse_qs(urlparse(resp.headers['location']).query)['code'][0]
        resp = _client().post('/oauth/token', data={
            'grant_type': 'authorization_code', 'code': code, 'code_verifier': verifier,
            'redirect_uri': 'https://claude.ai/api/mcp/auth_callback',
        })
        assert resp.status_code == 200, resp.text
        assert resp.json()['refresh_token']

    def test_login_form_carries_the_method_along(self):
        resp = _get('https://claude.ai/api/mcp/auth_callback')
        assert 'name="code_challenge_method" value="S256"' in resp.text

    def test_read_only_detour_keeps_pkce(self):
        """'Anderen Schlüssel eingeben' goes back via GET and must pass the checks."""
        resp = _post(
            'https://claude.ai/api/mcp/auth_callback',
            api_token='ijr_' + 'y' * 43, code_challenge_method='S256',
        )
        assert resp.status_code == 200
        assert resp.text.count('name="code_challenge_method" value="S256"') == 2


# ---------------------------------------------------------------------------
# Login page names a loopback target honestly
# ---------------------------------------------------------------------------

def test_loopback_target_is_described_as_a_program_on_this_computer():
    resp = _get('http://127.0.0.1:55352/callback/abc')
    assert 'Programm auf diesem Computer' in resp.text
