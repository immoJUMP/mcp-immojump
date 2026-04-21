# mcp-immojump

MCP server fuer die ImmoJUMP-Plattform — CRM, Pipelines, Immobilien,
Aktivitaeten und Dokumente direkt aus Claude.ai, Claude Desktop, ChatGPT
oder jedem anderen MCP-Client ansprechen.

Der Server ist absichtlich "thin": Alle Business-Regeln liegen im ImmoJUMP
Backend. Dieses Repo kapselt nur den MCP-Tool-Zugriff auf die bestehenden
API-Endpoints.

## Fuer Endnutzer (Claude.ai, Claude Desktop, ChatGPT)

1. In Claude.ai: Einstellungen → Connectors → Verbindung hinzufuegen
   (oder das Pendant im jeweiligen Client).
2. Server-URL eintragen:
   - Streamable HTTP: `https://mcp.immojump.de/mcp`
   - SSE (Claude Desktop): `https://mcp.immojump.de/sse`
3. Der Client leitet in den OAuth-Flow um. Dort eingeben:
   - **API-Token**: in immoJUMP unter *Einstellungen → API-Zugang → Token
     generieren*.
   - **Organisation-ID**: ist in der App-URL sichtbar, z. B.
     `https://immojump.de/o/<org-id>/…`.
4. Nach "Verbinden" ist der Connector einsatzbereit. Probiert z. B.:
   - *"Wie viele Immobilien habe ich?"*
   - *"Analysiere das Exposé und erstelle die Einheit in immoJUMP."*
   - *"Finde doppelte Kontakte und merge sie nach Rückfrage."*

Verfuegbar sind 87 Tools (Standard-Tier: Kontakte, Immobilien, Units,
Aktivitaeten, Pipelines, Statuses, Dokumente, Tags, Activity-Templates).
Die komplette Liste sieht man im Client nach der Verbindung oder mit
`npx @modelcontextprotocol/inspector https://mcp.immojump.de/mcp`.

## Scope

Abgedeckt (Standard-Tier, 87 Tools):

- Kontakte inkl. Import (Preview/Commit), Dubletten-Merge, Activities
- Immobilien inkl. Suche, Units, Milestones, Dokumente
- Pipeline- und Status-Management (CRUD, Reorder, Inbound-Aliases)
- Activity-Templates inkl. sicherem Outcome-Update mit Dry-Run
- Tags auf Entity-Ebene
- Dokumente listen / umbenennen / analysieren

Weitere Tier-Varianten existieren (`profi`, `full`) mit Deals, Tickets,
Custom Fields, E-Mail, Feed, Loans, Valuation, Org-Management.

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

Die aktuelle Liste steht im Code unter `src/mcp_immojump/tools/` und
wird zur Laufzeit vom Client abgefragt (`tools/list`). Schnellste
Uebersicht ohne Client-Setup:

```bash
npx @modelcontextprotocol/inspector https://mcp.immojump.de/mcp
```

Domain-Gliederung (je ein Modul unter `src/mcp_immojump/tools/`):

| Modul | Tools | Inhalt |
|-------|------:|--------|
| `connection` | 1 | Credential-Check |
| `immobilien` | 12 | Immobilien + Units-Split + Transfer |
| `units` | 5 | Einheiten pro Immobilie |
| `contacts` | 19 | CRUD, Import, Dubletten, Merge |
| `activities` | 11 | Aktivitaeten inkl. Property-Bindung |
| `activity_templates` | 8 | Workflow-Editor, Safe-Update |
| `pipelines` | 11 | Pipeline-CRUD + YAML-Import/Export |
| `statuses` | 6 | Status-CRUD, Reorder, Inbound-Aliases |
| `documents` | 8 | Dokumente listen / analysieren |
| `tags` | 6 | Tag-CRUD + Entity-Binding |

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

## Troubleshooting

### "Ungueltiger Token" / 401 beim OAuth-Login

- API-Token in immoJUMP neu generieren (Einstellungen → API-Zugang).
- Sicherstellen, dass der Token zur Organisation-ID passt, die im
  Formular eingetragen wurde. Die Org-ID steht in der App-URL nach
  `/o/` — nicht verwechseln mit einer Vertragsnummer o.ä.

### `403 Origin not allowed` beim Verbinden

Der Server akzeptiert nur Origins aus der Allowlist (`claude.ai`,
`claude.com`, `chatgpt.com`, `chat.openai.com`) und Loopback-Clients.
Andere Browser-Frontends muessen ueber die Umgebungsvariable
`IMMOJUMP_MCP_ALLOWED_ORIGINS` (comma-separated) freigegeben werden.

### `403 host_not_allowed` auf Edge-Ebene

Das kommt vom CDN / Edge-Firewall, nicht vom MCP-Server. Die
IP-Allowlist muss Anthropic-IPs enthalten, sonst laufen Connector-
Requests ins Leere. Referenz:
<https://support.claude.com/en/articles/12695044-anthropic-s-ip-ranges>.

### Kontakt-Import bleibt bei "running" haengen

- Job-Status prüfen: `contacts_job_status({ job_id })`.
- Bei serverseitigem Fehler: `contacts_job_resume({ job_id })` — läuft
  ab dem letzten Commit-Punkt weiter.
- Falls der Import abgebrochen werden muss: `contacts_job_cancel({ job_id })`.
  Bereits importierte Datensätze bleiben bestehen.

### Template-Update wirft `409`

Der optionale `data.if_updated_at`-Parameter stimmt nicht mehr mit dem
aktuellen `updated_at` des Templates überein — jemand anders hat das
Template zwischen Preview und Save geändert. Template neu laden
(`activity_template_get`) und das Update erneut anstoßen.

### `STATUS_CHANGE` im Outcome wird abgelehnt

- `target_status_id` ist Pflicht.
- Wenn `target_status_name` zusätzlich gesetzt ist, muss der Name zur
  ID passen — prüfen via `status_list`.

### Rate-Limits / Backend-Timeouts

Die Tools geben HTTP-Statuscodes direkt weiter. Bei `429` oder `5xx`
Tool-Aufruf manuell wiederholen; der Server selbst macht keinen
Auto-Retry, um doppelte Writes auszuschliessen.

## Security

Bitte beachten:

- Tokens nie ins Repo committen
- Nur freigegebene Base URLs verwenden
- Security Meldungen siehe `SECURITY.md`
