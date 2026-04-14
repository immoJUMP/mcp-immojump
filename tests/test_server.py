import pytest

import mcp_immojump.server as server


def test_resolve_credentials_requires_token_from_some_source(monkeypatch: pytest.MonkeyPatch):
    """Without any token source (param, contextvar, env), credentials must fail."""
    monkeypatch.setenv('IMMOJUMP_BASE_URL', 'http://localhost:8081')
    monkeypatch.delenv('IMMOJUMP_TOKEN', raising=False)
    monkeypatch.delenv('IMMOJUMP_ORGANISATION_ID', raising=False)

    with pytest.raises(ValueError):
        server._resolve_credentials(base_url=None, token=None, organisation_id='org-1')

    # organisation_id=None is allowed (for user_me, organisation_list)
    creds = server._resolve_credentials(base_url=None, token='abc', organisation_id=None)
    assert creds.token == 'abc'
    assert creds.organisation_id == ''


def test_resolve_credentials_falls_back_to_env_vars(monkeypatch: pytest.MonkeyPatch):
    """When params are None, credentials resolve from env vars."""
    monkeypatch.setenv('IMMOJUMP_BASE_URL', 'http://localhost:8081')
    monkeypatch.setenv('IMMOJUMP_TOKEN', 'env-token')
    monkeypatch.setenv('IMMOJUMP_ORGANISATION_ID', 'env-org')

    creds = server._resolve_credentials(base_url=None, token=None, organisation_id=None)
    assert creds.token == 'env-token'
    assert creds.organisation_id == 'env-org'


def test_resolve_credentials_param_overrides_env(monkeypatch: pytest.MonkeyPatch):
    """Explicit param takes precedence over env var."""
    monkeypatch.setenv('IMMOJUMP_BASE_URL', 'http://localhost:8081')
    monkeypatch.setenv('IMMOJUMP_TOKEN', 'env-token')
    monkeypatch.setenv('IMMOJUMP_ORGANISATION_ID', 'env-org')

    creds = server._resolve_credentials(base_url=None, token='param-token', organisation_id='param-org')
    assert creds.token == 'param-token'
    assert creds.organisation_id == 'param-org'


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
