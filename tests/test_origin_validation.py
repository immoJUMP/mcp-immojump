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
    'https://localhost:8443',  # dev HTTPS via mkcert/Caddy
])
def test_allowed_origins_accepted(origin: str) -> None:
    assert _is_origin_allowed(origin)


@pytest.mark.parametrize('origin', [
    'https://evil.example.com',
    'http://attacker.test',
    'https://claude.ai.evil.com',
    'http://10.0.0.5',
    # Http variants of public origins must be rejected
    'http://claude.ai',
    'http://chatgpt.com',
    # Origins with path / query / fragment are not valid per RFC 6454
    'http://localhost/evil',
    'http://localhost:8000/path',
    'http://localhost?x=1',
    'http://localhost#frag',
    # Empty string is not a valid origin
    '',
])
def test_disallowed_origins_rejected(origin: str) -> None:
    assert not _is_origin_allowed(origin)


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


def test_default_allowlist_has_no_dead_entries() -> None:
    """Guard against re-introducing origins that browsers never actually send."""
    from mcp_immojump.servers._base import _DEFAULT_ALLOWED_ORIGINS
    # Portless loopback entries are unreachable by real browsers; the
    # loopback fallback in _is_origin_allowed handles those cases.
    assert 'http://localhost' not in _DEFAULT_ALLOWED_ORIGINS
    assert 'http://127.0.0.1' not in _DEFAULT_ALLOWED_ORIGINS
