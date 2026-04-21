# Demo / Test Account Setup — for Anthropic Review

The Anthropic review team needs a live account with sample data to validate
the connector. Provide the information below in the submission form (Anthropic
treats it as confidential).

## 1. Account

| Field | Value |
|------|------|
| Platform URL | <https://beta.immojump.de> |
| Login e-mail | `anthropic-review@immojump.de` *(create before submitting)* |
| Password | *stored in 1Password vault `connectors-review`* |
| Organisation name | `Anthropic Review Sandbox` |
| Organisation ID | *fill in after creation — shown in URL, `/o/<id>/...`* |
| API token | *generate via Einstellungen → API-Zugang → Token generieren* |

Delete or disable the account 30 days after the connector goes live.

## 2. Seed data

Run the seed script inside the sandbox organisation to guarantee a reviewable
workspace:

```bash
# From the immojump backend repo
ENV=beta \
ORG_ID=<anthropic-review-org-id> \
python manage.py seed_demo_workspace --profile=mcp-review
```

The `mcp-review` profile creates:

- 50 contacts (mix of investor / seller / maker personas)
- 10 properties with units, documents, and milestones
- 3 pipelines (`Ankauf`, `Vermietung`, `Renovation`) with 5–7 statuses each
- 20 activities (past & future) and 5 activity templates
- 4 deals in different pipeline stages
- 6 open tickets + comments
- 3 custom-field definitions and views
- 5 loan records
- 10 e-mail threads (imported from a fixture mailbox)

Re-running the script wipes and reseeds the organisation — safe for test.

## 3. Connector setup flow (reviewer instructions)

1. In claude.ai → Settings → Connectors → Add connector.
2. Paste `https://mcp.immojump.de/mcp` (Streamable HTTP) or
   `https://mcp.immojump.de/sse` (SSE, Claude Desktop).
3. Complete the OAuth consent screen:
   - API token: *from §1*
   - Organisation ID: *from §1*
4. Claude Desktop / claude.ai stores the bearer and no further prompts
   ask for credentials.

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

- Cancel an import job (`contacts_job_cancel`) — must not destroy
  already-committed rows.
- Dry-run outcome replacement on an activity template (`dry_run=true`) —
  must return a diff and persist nothing.
- Concurrency guard (`if_updated_at`) — fake a mismatch and observe `409`.
- Origin header rejection — curl `-H "Origin: https://evil.example.com"` to
  `/mcp` and expect `403`.

## 6. Support during review

Live dev contact: `review@immojump.de` (SLA: next business day, Mon–Fri
09:00–18:00 CET). Escalation: CTO on `cto@immojump.de`.
