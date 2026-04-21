"""Shared helpers used by all server variants and tool modules.

Credential resolution order (per field):
1. Explicit tool parameter (if provided by Claude)
2. HTTP transport header (Authorization / X-Organisation-Id)
3. Environment variable (IMMOJUMP_TOKEN / IMMOJUMP_ORGANISATION_ID)

This means: if headers are configured in .mcp.json, tools work without
asking for credentials.  If not, Claude asks for them as tool parameters.
"""

from __future__ import annotations

import contextvars
import os
from typing import Any

from mcp.types import ToolAnnotations

from .client import ImmojumpAPIClient, ImmojumpCredentials


# ---------------------------------------------------------------------------
# MCP Tool annotation helpers
# ---------------------------------------------------------------------------
# The MCP spec's ToolAnnotations carry hints that clients use to build
# confirmation prompts and safety policies.  Each tool wraps a single HTTP
# verb on the ImmoJUMP backend, so classification is one of three cases:
#
# - read_only:     safe GET-like operations, no state change
# - write_op:      creates / updates, no deletion of existing records
# - destructive_op: deletes or otherwise irreversibly removes data
#
# idempotentHint is left unset by default because HTTP verb alone does not
# imply semantic idempotence — callers who know better should pass it in.

def read_only(title: str | None = None) -> ToolAnnotations:
    """Annotation for tools that only read data."""
    return ToolAnnotations(
        title=title,
        readOnlyHint=True,
        openWorldHint=True,
    )


def write_op(
    title: str | None = None,
    *,
    idempotent: bool | None = None,
) -> ToolAnnotations:
    """Annotation for tools that create or mutate data but do not delete."""
    return ToolAnnotations(
        title=title,
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=idempotent,
        openWorldHint=True,
    )


def destructive_op(
    title: str | None = None,
    *,
    idempotent: bool | None = None,
) -> ToolAnnotations:
    """Annotation for tools that delete or otherwise irreversibly destroy data."""
    return ToolAnnotations(
        title=title,
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=idempotent,
        openWorldHint=True,
    )


# ---------------------------------------------------------------------------
# Context variables – set by the ASGI middleware for HTTP transports
# ---------------------------------------------------------------------------

ctx_token: contextvars.ContextVar[str | None] = contextvars.ContextVar('immojump_token', default=None)
ctx_organisation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar('immojump_org_id', default=None)


# ---------------------------------------------------------------------------
# Server config helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Tool helpers
# ---------------------------------------------------------------------------

def _require_text(*, field_name: str, value: str | None) -> str:
    resolved = str(value or '').strip()
    if not resolved:
        raise ValueError(f'{field_name} is required')
    return resolved


def _require_dict(*, field_name: str, value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        # Some MCP clients (ChatGPT) send JSON-encoded strings instead of objects
        import json
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            pass
    if not isinstance(value, dict):
        raise ValueError(f'{field_name} must be an object')
    return value


def _require_list(*, field_name: str, value: Any) -> list[Any]:
    if isinstance(value, str):
        # Some MCP clients (ChatGPT) send JSON-encoded strings instead of arrays
        import json
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            pass
    if not isinstance(value, list):
        raise ValueError(f'{field_name} must be a list')
    return value


def _resolve_credentials(
    *,
    base_url: str | None,
    token: str | None,
    organisation_id: str | None,
) -> ImmojumpCredentials:
    """Resolve credentials with fallback chain: param → header → env var."""
    resolved_token = (
        _nonempty(token)
        or _nonempty(ctx_token.get())
        or _nonempty(os.getenv('IMMOJUMP_TOKEN'))
    )
    resolved_org = (
        _nonempty(organisation_id)
        or _nonempty(ctx_organisation_id.get())
        or _nonempty(os.getenv('IMMOJUMP_ORGANISATION_ID'))
    )
    return ImmojumpCredentials(
        base_url=base_url or os.getenv('IMMOJUMP_BASE_URL', ''),
        token=_require_text(field_name='token', value=resolved_token),
        organisation_id=resolved_org or '',  # May be empty for user_me/organisation_list
    )


def _nonempty(value: str | None) -> str | None:
    """Return value if non-empty string, else None."""
    if value and str(value).strip():
        return str(value).strip()
    return None


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
