"""End-to-end middleware tests — exercise _OAuthFrontMiddleware over ASGI."""

from __future__ import annotations

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from mcp_immojump.servers._base import _OAuthFrontMiddleware


def _dummy_mcp_app() -> Starlette:
    async def mcp_route(request):
        return PlainTextResponse('mcp-body')

    async def messages_route(request):
        return PlainTextResponse('messages-body')

    return Starlette(routes=[
        Route('/mcp', mcp_route, methods=['GET', 'POST']),
        Route('/sse', mcp_route, methods=['GET']),
        Route('/messages', messages_route, methods=['POST']),
        Route('/unrelated', mcp_route, methods=['GET']),
    ])


@pytest.fixture
def client() -> TestClient:
    app = _OAuthFrontMiddleware(_dummy_mcp_app())
    return TestClient(app)


def test_mcp_without_origin_returns_401(client: TestClient) -> None:
    # No auth, no origin → 401 with WWW-Authenticate (non-browser client)
    resp = client.get('/mcp')
    assert resp.status_code == 401
    assert resp.headers['www-authenticate'].startswith('Bearer ')


def test_mcp_with_allowed_origin_passes(client: TestClient) -> None:
    resp = client.get(
        '/mcp',
        headers={'Origin': 'https://claude.ai', 'Authorization': 'Bearer x'},
    )
    assert resp.status_code == 200
    assert resp.text == 'mcp-body'


def test_mcp_with_disallowed_origin_returns_403(client: TestClient) -> None:
    resp = client.get(
        '/mcp',
        headers={'Origin': 'https://evil.example.com', 'Authorization': 'Bearer x'},
    )
    assert resp.status_code == 403


def test_messages_with_disallowed_origin_returns_403(client: TestClient) -> None:
    resp = client.post(
        '/messages',
        headers={'Origin': 'https://evil.example.com', 'Authorization': 'Bearer x'},
    )
    assert resp.status_code == 403


def test_sse_with_disallowed_origin_returns_403(client: TestClient) -> None:
    resp = client.get(
        '/sse',
        headers={'Origin': 'https://evil.example.com', 'Authorization': 'Bearer x'},
    )
    assert resp.status_code == 403


def test_origin_check_not_applied_to_non_mcp_paths(client: TestClient) -> None:
    # The middleware only gates MCP paths; anything else is forwarded
    # untouched.  /unrelated is a non-MCP route, so a bad Origin is allowed
    # through.
    resp = client.get(
        '/unrelated',
        headers={'Origin': 'https://evil.example.com'},
    )
    assert resp.status_code == 200


def test_oauth_metadata_endpoint_is_routed(client: TestClient) -> None:
    resp = client.get('/.well-known/oauth-authorization-server')
    assert resp.status_code == 200
    assert 'authorization_endpoint' in resp.json()


def test_oauth_authorize_sets_security_headers(client: TestClient) -> None:
    resp = client.get(
        '/oauth/authorize',
        params={
            'client_id': 'x',
            'redirect_uri': 'https://claude.ai/callback',
            'state': 's',
            'code_challenge': 'c',
            'code_challenge_method': 'S256',
        },
    )
    assert resp.status_code == 200
    assert resp.headers['x-frame-options'] == 'DENY'
    assert "frame-ancestors 'none'" in resp.headers['content-security-policy']
    assert resp.headers['referrer-policy'] == 'no-referrer'
    assert resp.headers['x-content-type-options'] == 'nosniff'
