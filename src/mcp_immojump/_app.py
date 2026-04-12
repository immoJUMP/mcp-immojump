"""Shared MCP application instance and helpers.

All tool modules import from here to register tools on the same ``mcp``
instance.  ``server.py`` re-exports the helpers so existing tests keep
working without changes.
"""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import ImmojumpAPIClient, ImmojumpCredentials


def _resolve_mcp_host() -> str:
    return str(
        os.getenv('IMMOJUMP_MCP_HOST')
        or os.getenv('FASTMCP_HOST')
        or '127.0.0.1'
    ).strip()


def _resolve_mcp_port() -> int:
    raw = str(
        os.getenv('IMMOJUMP_MCP_PORT')
        or os.getenv('FASTMCP_PORT')
        or '8000'
    ).strip()
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'Invalid MCP port: {raw}') from exc


mcp = FastMCP(
    'immojump',
    host=_resolve_mcp_host(),
    port=_resolve_mcp_port(),
)


# ---------------------------------------------------------------------------
# Shared helpers used by every tool module
# ---------------------------------------------------------------------------

def _require_text(*, field_name: str, value: str | None) -> str:
    resolved = str(value or '').strip()
    if not resolved:
        raise ValueError(f'{field_name} is required')
    return resolved


def _require_dict(*, field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f'{field_name} must be an object')
    return value


def _require_list(*, field_name: str, value: Any) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f'{field_name} must be a list')
    return value


def _resolve_credentials(
    *,
    base_url: str | None,
    token: str | None,
    organisation_id: str | None,
) -> ImmojumpCredentials:
    return ImmojumpCredentials(
        base_url=base_url or os.getenv('IMMOJUMP_BASE_URL', ''),
        token=_require_text(field_name='token', value=token),
        organisation_id=_require_text(field_name='organisation_id', value=organisation_id),
    )


def _call_with_client(
    *,
    base_url: str | None,
    token: str | None,
    organisation_id: str | None,
    callback,
) -> Any:
    creds = _resolve_credentials(base_url=base_url, token=token, organisation_id=organisation_id)
    with ImmojumpAPIClient(creds) as client:
        return callback(client)


def _ok(result: Any) -> dict[str, Any]:
    return {'ok': True, 'result': result}
