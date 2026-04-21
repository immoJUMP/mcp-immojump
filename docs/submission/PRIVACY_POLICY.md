# Privacy Policy — immoJUMP MCP Connector (TEMPLATE)

> **TEMPLATE — NOT READY TO PUBLISH.** Every field marked `«TODO»` must be
> verified by the vendor before hosting this at a public URL. Do not submit
> the connector until this document reflects reality.

_Last updated: «TODO: date at publication»_

## 1. Who we are

«TODO: legal entity, address, managing director per §5 TMG»

Contact for privacy questions: «TODO: privacy@… »

## 2. What the connector does

The connector is a thin proxy between MCP clients (Claude.ai, Claude Desktop,
ChatGPT) and the existing immoJUMP REST API. It does not persist user data
in a separate database. All business data (contacts, properties, activities,
pipelines, documents) is stored in the user's immoJUMP organisation and
subject to the platform's main privacy policy at «TODO: link».

## 3. Data processed

| Category | Purpose | Retention |
|----------|---------|-----------|
| OAuth API tokens | Authenticate tool calls on behalf of the user | In-memory only for the session; access-token lifetime: 24 h per issuance |
| Authorization codes | Complete OAuth handshake | 5 minutes, in-memory |
| Request / response logs | Debugging, abuse prevention | «TODO: confirm actual retention window» |
| Business data (contacts, properties, etc.) | Fulfil tool call | Stored in immoJUMP backend per main policy |

The MCP connector performs no persistent storage of user content of its own.

## 4. Legal basis (GDPR)

- Art. 6 (1) (b) GDPR — performance of the contract the user holds with «TODO: legal entity».
- Art. 6 (1) (f) GDPR — legitimate interest in operating the service securely.

## 5. Sub-processors

- «TODO: hosting provider, location, DPA link»
- The MCP client the end user chose to connect (e.g. Anthropic PBC,
  OpenAI OpCo LLC). The model provider receives the tool arguments and
  results the user's prompt requires. The user controls this connection.

«TODO: confirm no other sub-processors.»

We do not sell personal data.

## 6. User rights

GDPR rights (access, rectification, erasure, restriction, portability,
objection) are exercised via the main immoJUMP account or by e-mailing
«TODO: privacy contact». Disconnecting the connector in the MCP client
revokes the OAuth grant; stored tokens are invalidated on the next reload.

## 7. Security

- Transport: HTTPS, «TODO: confirm TLS version minimum enforced at edge»
- Origin-Header validation against an allowlist (`claude.ai`, `claude.com`,
  `chatgpt.com`, `chat.openai.com`)
- OAuth 2.1 with PKCE (S256) and short-lived access tokens
- Backend calls restricted to an explicit base-URL allowlist
- No API keys in prompts or logs
- Vulnerability reports: see `SECURITY.md`

## 8. Changes

Material changes announced in the release notes at
«TODO: repo releases URL» and via in-product notification.
