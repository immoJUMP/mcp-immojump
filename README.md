# mcp-immojump

MCP server fuer ImmoJUMP Kontakte-Orchestrierung.

Der Server ist absichtlich "thin": Alle Business-Regeln liegen im ImmoJUMP
Backend. Dieses Repo kapselt nur den MCP-Tool-Zugriff auf die bestehenden API
Endpoints.

## Scope

Abgedeckt sind aktuell:

- Kontakt-Import als Preview und Commit
- Job-Status, Resume, Cancel
- Dubletten-Vorschau und Merge-Ausfuehrung

Nicht im Scope:

- Eigene Datenhaltung im MCP-Server
- Duplizierte Business-Logik

## Backend Endpoints (verbrauchte API)

- `POST /api/contacts/import-unified`
- `GET /api/contacts/import-jobs/<job_id>`
- `POST /api/contacts/import-jobs/<job_id>/resume`
- `POST /api/contacts/import-jobs/<job_id>/cancel`
- `GET /api/contacts/duplicates`
- `POST /api/contacts/merge`

## Allowlist fuer Base URLs

Nur diese ImmoJUMP URLs sind erlaubt:

- `http://localhost:8081`
- `https://beta.immojump.de`
- `https://immojump.de`

## Credentials

Credentials koennen pro Tool-Call uebergeben oder als Env gesetzt werden:

- `IMMOJUMP_BASE_URL`
- `IMMOJUMP_TOKEN`
- `IMMOJUMP_ORGANISATION_ID`

## Verfuegbare MCP Tools

- `connection_test`
- `contacts_import_preview`
- `contacts_import_start`
- `contacts_job_status`
- `contacts_job_resume`
- `contacts_job_cancel`
- `contacts_duplicates_preview`
- `contacts_merge_apply`

## Schnellstart (lokal)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[test]

export IMMOJUMP_BASE_URL=http://localhost:8081
export IMMOJUMP_TOKEN=<TOKEN>
export IMMOJUMP_ORGANISATION_ID=<ORG_ID>

mcp-immojump
```

## Transport-Modi

Default:

- `sse`

Codex-kompatibel:

```bash
export IMMOJUMP_MCP_TRANSPORT=streamable-http
mcp-immojump
```

Weitere Werte:

- `stdio`

## Codex CLI Beispiel

```bash
codex mcp add immojump-local --url http://127.0.0.1:8000/mcp
codex mcp list --json
```

Nach dem Test:

```bash
codex mcp remove immojump-local
```

## Import Best Practice

1. Immer zuerst `contacts_import_preview`
2. Preview pruefen (`create/update/skip`)
3. Dann `contacts_import_start`
4. Job pollen mit `contacts_job_status`
5. Bei Bedarf `contacts_job_resume` oder `contacts_job_cancel`

## Entwicklung

Tests:

```bash
PYTHONPATH=src pytest -q
```

Lint:

```bash
PYTHONPATH=src ruff check src tests
```

CI:

- GitHub Actions unter `.github/workflows/ci.yml`

## Security

Bitte beachten:

- Tokens nie ins Repo committen
- Nur freigegebene Base URLs verwenden
- Security Meldungen siehe `SECURITY.md`
