# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`mcp-immojump` is a **thin, stateless MCP server** for the immoJUMP platform: it
exposes the immoJUMP backend API (contacts, properties, units, activities,
pipelines, statuses, documents, tags, ...) as MCP tools. All business logic
stays in the backend — this repo only wraps the HTTP calls. Hosted at
`https://mcp.immojump.de/mcp` (Streamable HTTP) and `/sse`.

## Commands

```bash
pip install -e ".[test]"     # install with test extras (pytest, ruff)
PYTHONPATH=src pytest -q     # run tests
ruff check .                 # lint (line-length 100, target py311)
```

Entry points (`pyproject.toml` `[project.scripts]`): `mcp-immojump` (full),
`mcp-immojump-standard`, `mcp-immojump-profi`, plus domain-scoped servers
(`-properties`, `-crm`, `-pipeline`, `-org`).

## Architecture

- `src/mcp_immojump/server.py` — server entry; `servers/` holds the tier
  variants (`standard` / `profi` / `full`) and the domain servers.
- `src/mcp_immojump/tools/` — one module per entity (contacts, immobilien,
  units, activities, pipelines, documents, ...).
- `src/mcp_immojump/client.py` — `ImmojumpAPIClient` + `ImmojumpCredentials`.
- `src/mcp_immojump/_shared.py` — credential resolution + MCP tool annotations.
- `src/mcp_immojump/oauth.py` — interactive OAuth flow for end-user clients.

## Authentication

Credentials are resolved per field with a fallback chain — see
`_shared.py` `_resolve_credentials`:

1. Explicit tool parameter (passed by the MCP client).
2. HTTP transport header — `Authorization` (Bearer) and `X-Organisation-Id`.
   An ASGI middleware copies these into the `ctx_token` / `ctx_organisation_id`
   context variables.
3. Environment variable — `IMMOJUMP_TOKEN` / `IMMOJUMP_ORGANISATION_ID`.

With headers (or env vars) configured, every tool works without the
interactive OAuth flow (`oauth.py`). The server keeps no per-user session —
credentials travel with each request.
