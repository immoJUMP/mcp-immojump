# Landing Page Copy — `«TODO: public URL»/mcp` (TEMPLATE)

> **TEMPLATE.** Replace every `«TODO»` before publishing. Verify that the
> "Install in Claude" deep-link format currently used by claude.ai matches
> the `href` below; if not, fall back to a plain documentation link.

---

## Hero

**immoJUMP für Claude & ChatGPT**
Dein CRM, deine Pipelines und dein Immobilien-Portfolio — direkt im Chat.

*Primary CTA:* „In Claude.ai installieren"
→ «TODO: verified Claude connector install URL, or fall back to the docs page»

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
- «TODO: GDPR / hosting statement, only once verified»
- Security-Policy: siehe `SECURITY.md`

## So richtest du es ein

1. In claude.ai → Einstellungen → Connectors → Verbindung hinzufügen.
2. «TODO: öffentliche Server-URL» einfügen.
3. API-Token + Organisation-ID eingeben (einmalig).
4. Teste mit *„Zeig mir alle Kontakte mit Tag Investor."*

## FAQ

**Brauche ich eine Enterprise-Lizenz?** Nein. Jeder immoJUMP-Tarif mit API-
Zugang reicht.

**Wer sieht meine Daten?** Der User und der gewählte MCP-Client. Der MCP-
Server speichert keine Tokens über die Session hinaus.

**Kann ich den Connector selbst hosten?** Ja, das Repository ist MIT-lizenziert.
Siehe `Dockerfile` und `README.md`.

**Support:** «TODO: contact e-mail» · [GitHub Issues](https://github.com/immoJUMP/mcp-immojump/issues)

---

*Footer links:* Privacy Policy · Terms · GitHub · Status
