"""Origin header validation (DNS-rebind / CSRF protection)."""

from __future__ import annotations

import pytest

from mcp_immojump.servers._base import _allowed_origins, _is_origin_allowed


@pytest.mark.parametrize('origin', [
    'https://claude.ai',
    'https://claude.com',
    'https://chatgpt.com',
    'https://chat.openai.com',
    'http://localhost',
    'http://localhost:8000',
    'http://127.0.0.1:54321',
])
def test_allowed_origins_accepted(origin: str) -> None:
    assert _is_origin_allowed(origin)


@pytest.mark.parametrize('origin', [
    'https://evil.example.com',
    'http://attacker.test',
    'https://claude.ai.evil.com',
    'http://10.0.0.5',
    # http variants of public origins must be rejected
    'http://claude.ai',
    'http://chatgpt.com',
])
def test_disallowed_origins_rejected(origin: str) -> None:
    assert not _is_origin_allowed(origin)


def test_empty_origin_rejected_by_is_allowed() -> None:
    # _is_origin_allowed returns False for empty; the middleware treats
    # empty Origin as "no browser" and lets it through.
    assert not _is_origin_allowed('')


def test_env_extends_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('IMMOJUMP_MCP_ALLOWED_ORIGINS', 'https://example.org,https://foo.test/')
    allowed = _allowed_origins()
    assert 'https://example.org' in allowed
    assert 'https://foo.test' in allowed
    # Defaults are preserved
    assert 'https://claude.ai' in allowed


def test_env_allowlist_empty_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('IMMOJUMP_MCP_ALLOWED_ORIGINS', raising=False)
    allowed = _allowed_origins()
    assert 'https://claude.ai' in allowed
    assert 'https://example.org' not in allowed
