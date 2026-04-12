"""Tests for the OAuth 2.1 authorization wrapper."""

import base64
import hashlib
import secrets
from urllib.parse import urlparse, parse_qs

import pytest
from starlette.testclient import TestClient
from starlette.applications import Starlette

from mcp_immojump.oauth import (
    create_oauth_routes,
    decode_access_token,
    _encode_access_token,
    _verify_pkce,
    _auth_codes,
)


@pytest.fixture()
def oauth_client(monkeypatch):
    """Starlette test client with OAuth routes mounted.
    Points IMMOJUMP_BASE_URL to unreachable host so token validation is skipped."""
    monkeypatch.setenv('IMMOJUMP_BASE_URL', 'http://127.0.0.1:1')  # unreachable
    app = Starlette(routes=create_oauth_routes())
    return TestClient(app, base_url='https://mcp.immojump.de')


@pytest.fixture(autouse=True)
def _clear_codes():
    """Clear auth codes between tests."""
    _auth_codes.clear()
    yield
    _auth_codes.clear()


def _pkce_pair():
    """Generate a PKCE code_verifier + code_challenge pair."""
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode('ascii')).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')
    return verifier, challenge


# ---------------------------------------------------------------------------
# Token encoding / decoding
# ---------------------------------------------------------------------------

class TestTokenEncoding:
    def test_encode_decode_roundtrip(self):
        token = _encode_access_token('my-api-token', 'org-123')
        result = decode_access_token(token)
        assert result == ('my-api-token', 'org-123')

    def test_decode_invalid_base64(self):
        assert decode_access_token('not-valid!!!') is None

    def test_decode_missing_separator(self):
        token = base64.urlsafe_b64encode(b'no-separator').decode()
        assert decode_access_token(token) is None

    def test_decode_empty_parts(self):
        token = base64.urlsafe_b64encode(b':org').decode()
        assert decode_access_token(token) is None
        token2 = base64.urlsafe_b64encode(b'tok:').decode()
        assert decode_access_token(token2) is None

    def test_token_with_colons_in_api_token(self):
        """API tokens may contain colons — only split on first."""
        token = _encode_access_token('eyJ:complex:token', 'org-1')
        result = decode_access_token(token)
        assert result == ('eyJ:complex:token', 'org-1')


# ---------------------------------------------------------------------------
# PKCE verification
# ---------------------------------------------------------------------------

class TestPKCE:
    def test_valid_pkce(self):
        verifier, challenge = _pkce_pair()
        assert _verify_pkce(verifier, challenge) is True

    def test_invalid_pkce(self):
        _, challenge = _pkce_pair()
        assert _verify_pkce('wrong-verifier', challenge) is False

    def test_empty_verifier(self):
        assert _verify_pkce('', 'some-challenge') is False


# ---------------------------------------------------------------------------
# Discovery endpoints
# ---------------------------------------------------------------------------

class TestDiscovery:
    def test_protected_resource_metadata(self, oauth_client):
        resp = oauth_client.get('/.well-known/oauth-protected-resource')
        assert resp.status_code == 200
        data = resp.json()
        assert 'authorization_servers' in data
        assert len(data['authorization_servers']) >= 1
        assert 'bearer_methods_supported' in data
        assert 'header' in data['bearer_methods_supported']

    def test_authorization_server_metadata(self, oauth_client):
        resp = oauth_client.get('/.well-known/oauth-authorization-server')
        assert resp.status_code == 200
        data = resp.json()
        assert data['authorization_endpoint'].endswith('/oauth/authorize')
        assert data['token_endpoint'].endswith('/oauth/token')
        assert 'code' in data['response_types_supported']
        assert 'authorization_code' in data['grant_types_supported']
        assert 'S256' in data['code_challenge_methods_supported']

    def test_metadata_endpoints_are_consistent(self, oauth_client):
        """Auth server URL in resource metadata must match AS metadata issuer."""
        rm = oauth_client.get('/.well-known/oauth-protected-resource').json()
        asm = oauth_client.get('/.well-known/oauth-authorization-server').json()
        assert rm['authorization_servers'][0] == asm['issuer']


# ---------------------------------------------------------------------------
# Authorization endpoint
# ---------------------------------------------------------------------------

class TestAuthorize:
    def test_get_renders_form(self, oauth_client):
        resp = oauth_client.get('/oauth/authorize', params={
            'client_id': 'test-client',
            'redirect_uri': 'http://localhost:3000/callback',
            'state': 'abc123',
            'code_challenge': 'test-challenge',
            'code_challenge_method': 'S256',
            'response_type': 'code',
        })
        assert resp.status_code == 200
        assert 'immoJUMP' in resp.text
        assert 'api_token' in resp.text
        assert 'org_id' in resp.text

    def test_get_requires_redirect_uri(self, oauth_client):
        resp = oauth_client.get('/oauth/authorize')
        assert resp.status_code == 400

    def test_get_rejects_non_s256(self, oauth_client):
        resp = oauth_client.get('/oauth/authorize', params={
            'redirect_uri': 'http://localhost:3000/callback',
            'code_challenge_method': 'plain',
        })
        assert resp.status_code == 400

    def test_post_generates_code_and_redirects(self, oauth_client):
        resp = oauth_client.post('/oauth/authorize', data={
            'api_token': 'test-token',
            'org_id': 'org-123',
            'redirect_uri': 'http://localhost:3000/callback',
            'state': 'mystate',
            'code_challenge': 'test-challenge',
            'client_id': 'test',
        }, follow_redirects=False)
        assert resp.status_code == 302
        location = resp.headers['location']
        assert location.startswith('http://localhost:3000/callback')
        params = parse_qs(urlparse(location).query)
        assert 'code' in params
        assert params['state'] == ['mystate']

    def test_post_requires_token_and_org(self, oauth_client):
        resp = oauth_client.post('/oauth/authorize', data={
            'api_token': '',
            'org_id': '',
            'redirect_uri': 'http://localhost:3000/callback',
        }, follow_redirects=False)
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Token endpoint
# ---------------------------------------------------------------------------

class TestTokenExchange:
    def _get_code(self, oauth_client, verifier=None, challenge=None):
        """Helper: submit authorize form and extract the code."""
        resp = oauth_client.post('/oauth/authorize', data={
            'api_token': 'my-api-token',
            'org_id': 'my-org-id',
            'redirect_uri': 'http://localhost:3000/callback',
            'state': 'test',
            'code_challenge': challenge or '',
            'client_id': 'test',
        }, follow_redirects=False)
        location = resp.headers['location']
        params = parse_qs(urlparse(location).query)
        return params['code'][0]

    def test_exchange_without_pkce(self, oauth_client):
        """Token exchange works when no PKCE challenge was set."""
        code = self._get_code(oauth_client)
        resp = oauth_client.post('/oauth/token', data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': 'http://localhost:3000/callback',
        })
        assert resp.status_code == 200
        data = resp.json()
        assert 'access_token' in data
        assert data['token_type'] == 'bearer'
        # Verify access_token decodes correctly
        decoded = decode_access_token(data['access_token'])
        assert decoded == ('my-api-token', 'my-org-id')

    def test_exchange_with_valid_pkce(self, oauth_client):
        """Token exchange succeeds with correct PKCE verifier."""
        verifier, challenge = _pkce_pair()
        code = self._get_code(oauth_client, verifier=verifier, challenge=challenge)
        resp = oauth_client.post('/oauth/token', data={
            'grant_type': 'authorization_code',
            'code': code,
            'code_verifier': verifier,
        })
        assert resp.status_code == 200
        assert 'access_token' in resp.json()

    def test_exchange_with_wrong_pkce_fails(self, oauth_client):
        """Token exchange fails with wrong PKCE verifier."""
        _, challenge = _pkce_pair()
        code = self._get_code(oauth_client, challenge=challenge)
        resp = oauth_client.post('/oauth/token', data={
            'grant_type': 'authorization_code',
            'code': code,
            'code_verifier': 'totally-wrong-verifier',
        })
        assert resp.status_code == 400
        assert resp.json()['error'] == 'invalid_grant'

    def test_exchange_without_pkce_when_required_fails(self, oauth_client):
        """If challenge was set, verifier is required."""
        _, challenge = _pkce_pair()
        code = self._get_code(oauth_client, challenge=challenge)
        resp = oauth_client.post('/oauth/token', data={
            'grant_type': 'authorization_code',
            'code': code,
            # no code_verifier!
        })
        assert resp.status_code == 400

    def test_code_cannot_be_reused(self, oauth_client):
        """Authorization codes are single-use."""
        code = self._get_code(oauth_client)
        # First exchange succeeds
        resp1 = oauth_client.post('/oauth/token', data={
            'grant_type': 'authorization_code', 'code': code,
        })
        assert resp1.status_code == 200
        # Second exchange fails
        resp2 = oauth_client.post('/oauth/token', data={
            'grant_type': 'authorization_code', 'code': code,
        })
        assert resp2.status_code == 400

    def test_expired_code_fails(self, oauth_client):
        """Expired auth codes must be rejected."""
        code = self._get_code(oauth_client)
        # Manually expire the code
        _auth_codes[code]['expires'] = 0
        resp = oauth_client.post('/oauth/token', data={
            'grant_type': 'authorization_code', 'code': code,
        })
        assert resp.status_code == 400

    def test_wrong_grant_type_fails(self, oauth_client):
        resp = oauth_client.post('/oauth/token', data={
            'grant_type': 'client_credentials',
        })
        assert resp.status_code == 400
        assert resp.json()['error'] == 'unsupported_grant_type'

    def test_invalid_code_fails(self, oauth_client):
        resp = oauth_client.post('/oauth/token', data={
            'grant_type': 'authorization_code',
            'code': 'nonexistent-code',
        })
        assert resp.status_code == 400

    def test_redirect_uri_mismatch_fails(self, oauth_client):
        code = self._get_code(oauth_client)
        resp = oauth_client.post('/oauth/token', data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': 'http://evil.example.com/steal',
        })
        assert resp.status_code == 400

    def test_json_body_accepted(self, oauth_client):
        """Token endpoint must accept both form and JSON bodies."""
        code = self._get_code(oauth_client)
        resp = oauth_client.post('/oauth/token', json={
            'grant_type': 'authorization_code',
            'code': code,
        })
        assert resp.status_code == 200
