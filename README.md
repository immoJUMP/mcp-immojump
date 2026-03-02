# mcp-immojump

MCP server fuer ImmoJUMP Kontakte- und Pipeline-Orchestrierung.

Der Server ist absichtlich "thin": Alle Business-Regeln liegen im ImmoJUMP
Backend. Dieses Repo kapselt nur den MCP-Tool-Zugriff auf die bestehenden API
Endpoints.

## Scope

Abgedeckt sind aktuell:

- Kontakt-Import als Preview und Commit
- Job-Status, Resume, Cancel
- Dubletten-Vorschau und Merge-Ausfuehrung
- Pipeline-Management (CRUD, Import/Export)
- Status-Management (CRUD, Reorder, Inbound-Aliases)
- Activity-Template-Management fuer den Workflow-Editor

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
- `GET /api/pipelines/<orga_id>/pipelines/count`
- `GET|POST /api/pipelines/<orga_id>/pipelines`
- `GET|PUT|DELETE /api/pipelines/pipelines/<pipeline_id>`
- `GET|POST /api/pipelines/pipelines/<pipeline_id>/statuses`
- `DELETE /api/pipelines/pipelines/<pipeline_id>/statuses/<status_id>`
- `GET /api/pipelines/pipelines/<pipeline_id>/export`
- `POST /api/pipelines/pipelines/import`
- `GET /api/statuses/statuses`
- `PUT|DELETE /api/statuses/statuses/<status_id>`
- `PUT /api/statuses/statuses/swap/<current_status_id>/<target_status_id>`
- `GET|POST /api/statuses/statuses/<status_id>/inbound-aliases`
- `GET|POST /api/activity-templates/activity_templates`
- `GET /api/activity-templates/activity_templates/recurring`
- `GET /api/activity-templates/activity_templates/status/<status_id>`
- `GET|PUT|DELETE /api/activity-templates/activity_templates/<template_id>`
- `POST /api/activity-templates/activity_templates/status/batch_move`

## Allowlist fuer Base URLs

Nur diese ImmoJUMP URLs sind erlaubt:

- `http://localhost:8081`
- `https://beta.immojump.de`
- `https://immojump.de`

## Credentials

Credentials werden pro Tool-Call uebergeben:

- `base_url` (optional; fallback: `IMMOJUMP_BASE_URL`)
- `token` (required)
- `organisation_id` (required)

Hinweis: Der Server speichert keine Tokens. `token` und `organisation_id` muessen
bei jedem Tool-Call gesetzt werden.

## Verfuegbare MCP Tools

- `connection_test`
- `contacts_import_preview`
- `contacts_import_start`
- `contacts_job_status`
- `contacts_job_resume`
- `contacts_job_cancel`
- `contacts_duplicates_preview`
- `contacts_merge_apply`
- `pipeline_count`
- `pipeline_list`
- `pipeline_get`
- `pipeline_create`
- `pipeline_update`
- `pipeline_delete`
- `pipeline_export`
- `pipeline_import`
- `pipeline_statuses_list`
- `pipeline_status_create`
- `pipeline_status_delete`
- `status_list`
- `status_update`
- `status_delete`
- `status_swap_order`
- `status_inbound_aliases_list`
- `status_inbound_alias_create`
- `activity_templates_list`
- `activity_templates_recurring_list`
- `activity_templates_by_status`
- `activity_template_get`
- `activity_template_create`
- `activity_template_update`
- `activity_template_delete`
- `activity_templates_batch_move`

## Safe Update fuer `activity_template_update`

`activity_template_update` unterstuetzt eine sichere Update-Semantik fuer
`outcomes/actions`:

- Wenn `data.outcomes` fehlt:
  - Outcomes bleiben unveraendert.
- Wenn `data.outcomes` vorhanden ist:
  - Standard ist Merge nach `outcome.id` (kein Full-Replace).
- Full-Replace nur mit:
  - `data.replace_outcomes: true`
- Optionaler Concurrency-Guard:
  - `data.if_updated_at: "<iso-timestamp>"`
  - liefert `409`, wenn der Datensatz zwischenzeitlich geaendert wurde.
- Optionales Preview:
  - `data.dry_run: true`
  - liefert strukturiertes Diff, ohne zu speichern.

Zusatzvalidierung auf Action-Ebene:

- `STATUS_CHANGE` erfordert `target_status_id`.
- Falls `target_status_name` mitgegeben wird, muss der Name zur ID passen.
- `CREATE_ACTIVITY` mit `template_id` wird auf Existenz und Organisationsscope
  validiert.

### Beispiel: Nur Titel aendern (Outcomes bleiben unveraendert)

```json
{
  "template_id": "a7d0f0b2-...",
  "data": {
    "title": "Neuer Titel",
    "description": "Textupdate"
  }
}
```

### Beispiel: Einen Outcome mergen (ohne Full-Replace)

```json
{
  "template_id": "a7d0f0b2-...",
  "data": {
    "outcomes": [
      {
        "id": "f2c0a8c1-...",
        "label": "Absage final"
      }
    ]
  }
}
```

### Beispiel: Vollstaendiges Replace der Outcomes

```json
{
  "template_id": "a7d0f0b2-...",
  "data": {
    "replace_outcomes": true,
    "outcomes": [
      {
        "id": "9f8f9c57-...",
        "key": "archive",
        "label": "Archivieren",
        "actions": [
          {
            "type": "STATUS_CHANGE",
            "target_status_id": 17
          }
        ]
      }
    ]
  }
}
```

### Beispiel: Dry-Run mit Concurrency-Guard

```json
{
  "template_id": "a7d0f0b2-...",
  "data": {
    "if_updated_at": "2026-03-02T10:00:00+00:00",
    "dry_run": true,
    "outcomes": [
      {
        "id": "f2c0a8c1-...",
        "label": "Absage final"
      }
    ]
  }
}
```

## Schnellstart (lokal)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[test]

export IMMOJUMP_BASE_URL=http://localhost:8081

mcp-immojump
```

## Docker (lokal)

Image bauen:

```bash
docker build -t mcp-immojump:local .
```

Container starten:

```bash
docker run --rm -p 8000:8000 \
  -e IMMOJUMP_BASE_URL=https://immojump.de \
  -e IMMOJUMP_MCP_TRANSPORT=streamable-http \
  -e IMMOJUMP_MCP_HOST=0.0.0.0 \
  -e IMMOJUMP_MCP_PORT=8000 \
  mcp-immojump:local
```

Hinweis:

- `token` und `organisation_id` werden weiterhin pro Tool-Call uebergeben.
- Der Container lauscht standardmaessig auf `0.0.0.0:8000`.

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
