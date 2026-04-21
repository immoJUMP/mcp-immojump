# Privacy Policy — immoJUMP MCP Connector

_Last updated: 2026-04-21_

This document is a template. Host the final version at a public URL
(e.g. `https://immojump.de/legal/privacy-mcp`) before submitting the
connector to the Anthropic Software Directory.

## 1. Who we are

ImmoJUMP GmbH operates the immoJUMP platform for real estate investors and the
corresponding Model Context Protocol (MCP) server at
`https://mcp.immojump.de`. For questions, contact `privacy@immojump.de`.

## 2. What the connector does

The connector is a thin proxy between MCP clients (Claude.ai, Claude Desktop,
ChatGPT) and the existing immoJUMP REST API. It does not store user data of
its own. All business data (contacts, properties, activities, pipelines,
documents) is stored inside the user's immoJUMP organisation and subject to
the platform's main privacy policy.

## 3. Data processed

| Category | Purpose | Retention |
|----------|---------|-----------|
| OAuth API tokens | Authenticate tool calls on behalf of the user | In-memory only, max 24 h per session |
| Authorization codes | Complete OAuth handshake | 5 minutes, in-memory |
| Request / response logs | Debugging, abuse prevention | 30 days, rotated |
| Business data (contacts, properties, etc.) | Fulfil tool call | Stored in immoJUMP backend per main policy |

The MCP connector performs **no** persistent storage of user content.

## 4. Legal basis (GDPR)

- Art. 6 (1) (b) GDPR — performance of the contract the user holds with ImmoJUMP GmbH.
- Art. 6 (1) (f) GDPR — legitimate interest in operating the service securely.

## 5. Sub-processors

- Hetzner Online GmbH — hosting inside the EU (Germany).
- Anthropic PBC / OpenAI OpCo, LLC — the MCP client the end user connected.
  Model providers receive the tool call arguments and results needed to
  satisfy the user's prompt. The user controls this by installing the
  connector.

We do not sell personal data.

## 6. User rights

GDPR rights (access, rectification, erasure, restriction, portability,
objection) are exercised via the main immoJUMP account (profile → privacy
centre) or by e-mailing `privacy@immojump.de`. Disconnecting the MCP
connector in claude.ai revokes the OAuth grant; tokens are invalidated on
the next reload.

## 7. Security

- Transport: TLS 1.2+
- Origin-Header validation against an allowlist (`claude.ai`, `claude.com`,
  `chatgpt.com`, `chat.openai.com`)
- OAuth with PKCE (S256) and short-lived access tokens
- Backend calls restricted to an explicit base-URL allowlist
- No API keys in prompts or logs
- Vulnerability reports: `security@immojump.de` — see `SECURITY.md`

## 8. Changes

Material changes will be announced in the connector's release notes at
`https://github.com/immoJUMP/mcp-immojump/releases` and via in-product
notification.
