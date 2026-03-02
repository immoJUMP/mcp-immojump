import pytest

import mcp_immojump.server as server


def test_resolve_credentials_requires_explicit_token_and_org(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('IMMOJUMP_BASE_URL', 'http://localhost:8081')
    monkeypatch.setenv('IMMOJUMP_TOKEN', 'env-token')
    monkeypatch.setenv('IMMOJUMP_ORGANISATION_ID', 'env-org')

    with pytest.raises(ValueError):
        server._resolve_credentials(base_url=None, token=None, organisation_id='org-1')

    with pytest.raises(ValueError):
        server._resolve_credentials(base_url=None, token='abc', organisation_id=None)


def test_resolve_credentials_uses_env_base_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('IMMOJUMP_BASE_URL', 'http://localhost:8081')
    creds = server._resolve_credentials(base_url=None, token='abc', organisation_id='org-1')
    assert creds.base_url == 'http://localhost:8081'


def test_resolve_mcp_port_reads_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('IMMOJUMP_MCP_PORT', '18000')
    assert server._resolve_mcp_port() == 18000


def test_resolve_mcp_port_rejects_invalid_value(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('IMMOJUMP_MCP_PORT', 'not-a-number')
    with pytest.raises(ValueError):
        server._resolve_mcp_port()
