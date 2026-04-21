# Demo / Test Account Setup — for Anthropic Review (TEMPLATE)

> Every `«TODO»` is a vendor decision that must be filled in before the
> submission form is opened. Do not hand this document to Anthropic until
> the seed script, account, and contacts actually exist.

The reviewer needs a live account with sample data. Provide the following
in the submission form (Anthropic treats it confidentially).

## 1. Account

| Field | Value |
|------|------|
| Platform URL | `https://beta.immojump.de` (staging) — or `https://immojump.de` (prod) |
| MCP server URL | `https://mcp.immojump.de/mcp` (Streamable HTTP) / `https://mcp.immojump.de/sse` (SSE) |
| Login e-mail | «TODO: create a dedicated review account» |
| Password | «TODO: store in your password manager; share only via the submission form» |
| Organisation name | «TODO: e.g. Anthropic Review Sandbox» |
| Organisation ID | «TODO: fill in after creation (visible in URL `/o/<id>/…`)» |
| API token | «TODO: generate via Einstellungen → API-Zugang → Token generieren» |

Rotate or disable the account after the connector goes live.

## 2. Seed data

The backend repo should expose a seeding command that populates the
sandbox organisation with reviewable demo data. If no such command exists
yet, create one covering at minimum:

- Contacts with a variety of tags and statuses
- Properties with units, documents, milestones
- Pipelines (`Ankauf`, `Vermietung`, `Renovation`) with several statuses each
- Activities (past & future) and activity templates
- Deals in different pipeline stages
- Tickets with comments
- Custom-field definitions and views
- Loans
- E-mail threads (fixture mailbox)

«TODO: document the exact command (repo + invocation) and the resulting
data volumes.»

## 3. Connector setup flow (reviewer instructions)

1. In claude.ai → Settings → Connectors → Add connector.
2. Paste `https://mcp.immojump.de/mcp` (Streamable HTTP) or
   `https://mcp.immojump.de/sse` (SSE) for Claude Desktop.
3. Complete the OAuth consent screen:
   - API token: *from §1*
   - Organisation ID: *from §1*
4. The client stores the bearer token; no further prompts ask for credentials.

## 4. Golden-path prompts to try

| Area | Prompt |
|------|--------|
| Smoke test | "Teste die Verbindung zu immoJUMP." |
| CRM | "Zeig mir alle Kontakte mit Tag `Investor` und erstelle eine Aktivität `Call` für morgen." |
| Pipelines | "Liste alle Pipelines und exportiere die `Ankauf`-Pipeline als YAML." |
| Properties | "Suche Immobilien mit Status `Im Angebot` und zeig die verknüpften Kontakte." |
| Duplicate hygiene | "Finde doppelte Kontakte und merge sie nach Rückfrage." |
| Safe update | "Benenne den Outcome `Absage` der Template-ID … um — ohne Vollersatz." |

## 5. Edge cases to validate

- Cancel an import job (`contacts_job_cancel`) — already-committed rows
  must survive.
- Dry-run outcome replacement on an activity template (`dry_run=true`) —
  returns a diff, persists nothing.
- Concurrency guard (`if_updated_at`) — mismatch returns `409`.
- Origin header rejection — a request with `Origin: https://evil.example.com`
  to `/mcp` must return `403`.

## 6. Support during review

Primary contact: `info@immojump.de`

«TODO: optional — name a live dev contact, working hours, and an
escalation path for Anthropic.»
