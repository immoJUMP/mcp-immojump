# Landing Page Copy — `immojump.de/mcp`

Marketing stub for the public page that has to exist before submitting.
Drop the sections below into the CMS at `/mcp`.

---

## Hero

**immoJUMP für Claude & ChatGPT**
Dein CRM, deine Pipelines und dein Immobilien-Portfolio — direkt im Chat.

*Primary CTA:* „In Claude.ai installieren"  →  deep link
`https://claude.ai/connectors/new?name=immojump&url=https://mcp.immojump.de/mcp`

*Secondary CTA:* „Dokumentation ansehen"  →  link to help-center article

## Was der Connector kann

- Kontakte anlegen, mergen und dedupen aus natürlicher Sprache
- Pipelines & Statuspläne lesen, exportieren, importieren (YAML/JSON)
- Immobilien finden, Units verwalten, Milestones setzen
- Aktivitäten & Termine als Task, Decision oder wiederkehrend planen
- Activity-Templates sicher updaten — mit Dry-Run und Concurrency-Guard
- Dokumente listen, analysieren und markieren
- Loans, Tickets, Deals, Custom Fields, E-Mail, Feed, Org-Management

Das alles mit **170 Tools**, aufgeteilt in drei Paketen: `standard`
(Investor-Kern), `profi` (plus Deals/Tickets/Custom Fields) und `full`.

## Sicherheit

- OAuth 2.1 (PKCE) — dein API-Token verlässt den Browser nicht
- Origin-Header-Validierung gegen Claude.ai, ChatGPT und Localhost-Clients
- First-Party-API: keine Daten werden an Dritte weitergegeben
- GDPR-konform, Hosting in der EU (Hetzner DE)
- Öffentliches Security-Policy: `SECURITY.md`

## So richtest du es ein

1. In claude.ai → Einstellungen → Connectors → Verbindung hinzufügen.
2. `https://mcp.immojump.de/mcp` einfügen.
3. Dein immoJUMP-API-Token + Organisation-ID eingeben (einmalig).
4. Fertig — teste es mit *„Zeig mir alle Kontakte mit Tag Investor."*

## FAQ

**Brauche ich eine Enterprise-Lizenz?** Nein. Jeder immoJUMP-Tarif mit API-
Zugang funktioniert.

**Wer sieht meine Daten?** Nur du und der MCP-Client, den du verbunden hast.
Die immoJUMP-Server speichern keine Tokens über die Session hinaus.

**Kann ich den Connector selbst hosten?** Ja, das Repository ist MIT-lizenziert.
Siehe `Dockerfile` und `README.md`.

**Support:** `connectors@immojump.de` · [GitHub Issues](https://github.com/immoJUMP/mcp-immojump/issues)

---

*Footer links:* Privacy Policy · Terms · GitHub · Status
