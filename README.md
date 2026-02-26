# mcp-immojump

MCP server for ImmoJUMP contacts orchestration.

## Scope

This server is intentionally thin and delegates all contact business logic to the ImmoJUMP backend API:

- `POST /api/contacts/import-unified`
- `GET /api/contacts/import-jobs/<job_id>`
- `POST /api/contacts/import-jobs/<job_id>/resume`
- `POST /api/contacts/import-jobs/<job_id>/cancel`
- `GET /api/contacts/duplicates`
- `POST /api/contacts/merge`

## Allowed Base URLs

Only these API base URLs are accepted:

- `http://localhost:8081`
- `https://beta.immojump.de`
- `https://immojump.de`

## Credentials

Each tool can receive credentials explicitly, or via env vars:

- `IMMOJUMP_BASE_URL`
- `IMMOJUMP_TOKEN`
- `IMMOJUMP_ORGANISATION_ID`

## Tools

- `connection_test`
- `contacts_import_preview`
- `contacts_import_start`
- `contacts_job_status`
- `contacts_job_resume`
- `contacts_job_cancel`
- `contacts_duplicates_preview`
- `contacts_merge_apply`

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
export IMMOJUMP_BASE_URL=http://localhost:8081
export IMMOJUMP_TOKEN=...
export IMMOJUMP_ORGANISATION_ID=...
mcp-immojump
```

Default transport is `sse`.

To run Codex-compatible HTTP transport:

```bash
export IMMOJUMP_MCP_TRANSPORT=streamable-http
mcp-immojump
```

Supported values:
- `sse`
- `streamable-http`
- `stdio`

## Test

```bash
pytest -q
```

## Quality

- Lint: `ruff check src tests`
- CI: GitHub Actions workflow in `.github/workflows/ci.yml`
