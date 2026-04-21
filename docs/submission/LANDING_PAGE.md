# Landing Page Copy — `https://immojump.de` (TEMPLATE)

> Copy ready for the public landing page at `https://immojump.de`.
> Verify the Claude connector install URL format before going live;
> if it changes, fall back to a plain docs link.

---

## Hero

**immoJUMP für Claude & ChatGPT**
Dein CRM, deine Pipelines und dein Immobilien-Portfolio — direkt im Chat.

*Primary CTA:* „In Claude.ai installieren"
→ «TODO: verified Claude connector install URL; pass `https://mcp.immojump.de/mcp` as the server URL»

*Secondary CTA:* „Dokumentation ansehen"
→ «TODO: link to help-center article»

## Was der Connector kann

- Kontakte anlegen, mergen und dedupen aus natürlicher Sprache
- Pipelines & Statuspläne lesen, exportieren, importieren (YAML/JSON)
- Immobilien finden, Units verwalten, Milestones setzen
- Aktivitäten & Termine als Task, Decision oder wiederkehrend planen
- Activity-Templates sicher updaten — mit Dry-Run und Concurrency-Guard
- Dokumente listen, analysieren und markieren
- Loans, Tickets, Deals, Custom Fields, E-Mail, Feed, Org-Management

Insgesamt 170 Tools, aufgeteilt in drei Paketen: `standard` (Investor-Kern,
87 Tools), `profi` (plus Deals/Tickets/Custom Fields, 129 Tools) und `full`
(alle 170 Tools).

## Sicherheit

- OAuth 2.1 (PKCE) — der API-Token verlässt den Browser nicht
- Origin-Header-Validierung gegen Claude.ai, ChatGPT und Loopback-Clients
- First-Party-API: keine Weitergabe an Dritte außer dem gewählten MCP-Client
- Hosting in Deutschland bei Hetzner Online GmbH, DSGVO-konform
- Security-Policy: siehe `SECURITY.md`

## So richtest du es ein

1. In claude.ai → Einstellungen → Connectors → Verbindung hinzufügen.
2. `https://mcp.immojump.de/mcp` einfügen.
3. API-Token + Organisation-ID eingeben (einmalig).
4. Teste mit *„Zeig mir alle Kontakte mit Tag Investor."*

Für Claude Desktop verwende stattdessen `https://mcp.immojump.de/sse`.

## FAQ

**Brauche ich eine Enterprise-Lizenz?** Nein. Jeder immoJUMP-Tarif mit API-
Zugang reicht.

**Wer sieht meine Daten?** Der User und der gewählte MCP-Client. Der MCP-
Server speichert keine Tokens über die Session hinaus.

**Kann ich den Connector selbst hosten?** Ja, das Repository ist MIT-lizenziert.
Siehe `Dockerfile` und `README.md`.

**Support:** `info@immojump.de` · [GitHub Issues](https://github.com/immoJUMP/mcp-immojump/issues)

---

*Footer links:* [Datenschutz](https://immojump.de/ng/datenschutz) · [AGB](https://immojump.de/ng/agb) · [Impressum](https://immojump.de/ng/impressum) · [GitHub](https://github.com/immoJUMP/mcp-immojump)
