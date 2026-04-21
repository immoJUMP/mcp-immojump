# Anthropic Software Directory — Submission Checklist

Use this as the single source of truth before filling out
<https://clau.de/mcp-directory-submission>.

Scope: remote MCP server (hosted at `https://mcp.immojump.de`). The `.mcpb`
desktop bundle is **not** being submitted.

---

## 1. Basic metadata

| Field | Value |
|------|------|
| Connector name | `immoJUMP` |
| Tagline | CRM, pipelines & property operations for real-estate investors |
| Category | Productivity / CRM |
| Vendor | ImmoJUMP GmbH |
| Contact e-mail | `connectors@immojump.de` *(fill in)* |
| Support e-mail | `support@immojump.de` *(fill in)* |
| Public landing page | `https://immojump.de/mcp` *(stub: `docs/submission/LANDING_PAGE.md`)* |
| Server URL (Streamable HTTP) | `https://mcp.immojump.de/mcp` |
| Server URL (SSE) | `https://mcp.immojump.de/sse` |
| OAuth metadata URL | `https://mcp.immojump.de/.well-known/oauth-protected-resource` |
| Privacy Policy URL | `https://immojump.de/legal/privacy-mcp` *(template: `PRIVACY_POLICY.md`)* |
| Terms of Service URL | `https://immojump.de/legal/terms` |

## 2. Auth & transport (Review Criteria)

- [x] **OAuth 2.1** with PKCE (S256) — `src/mcp_immojump/oauth.py`
- [x] Dynamic Client Registration (RFC 7591) — `/oauth/register`
- [x] Protected-resource metadata (RFC 9728) — `/.well-known/oauth-protected-resource`
- [x] Authorization-server metadata (RFC 8414) — `/.well-known/oauth-authorization-server`
- [x] HTTPS-only in production — enforced at edge (ALB / reverse proxy)
- [x] Origin-Header validation — `_OAuthFrontMiddleware._is_origin_allowed`
- [x] No API keys in prompt — credentials exchanged via OAuth flow, never leaked to model
- [x] Base URL allowlist (`ALLOWED_BASE_URLS` in `client.py`)

## 3. Tool design (Review Criteria)

- [x] Every tool carries either `readOnlyHint=True` or `destructiveHint` via `ToolAnnotations` (helpers in `_shared.py`)
- [x] No tool mixes GET + POST/PUT/DELETE semantics — each tool wraps a single client method
- [x] All tool names ≤ 64 characters (longest: 34)
- [x] Descriptions contain no hidden / injection-style instructions
- [x] First-party only — the server calls ImmoJUMP's own APIs; no third-party data passthrough

## 4. Content & policy

- [x] No money transfers
- [x] No cryptocurrency
- [x] No AI-generated media
- [x] Legitimate proprietor — ImmoJUMP GmbH owns the backing API
- [x] Acceptance of [Directory Policy](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy)
- [x] Acceptance of [Directory Terms](https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms)

## 5. Deliverables uploaded in the form

- [ ] Public documentation URL (`https://immojump.de/mcp`)
- [ ] Privacy Policy URL (see `PRIVACY_POLICY.md`)
- [ ] Demo / test account credentials and setup script (see `DEMO_ACCOUNT.md`)
- [ ] Logo assets — SVG + PNG at 512 × 512 (`docs/submission/branding/`)
- [ ] 2-3 short screenshots of the connector in use (claude.ai)
- [ ] Short walk-through video (optional, <2 min)

## 6. Pre-flight validation

```bash
# schema check
claude plugin validate
# manual smoke test
npx @modelcontextprotocol/inspector https://mcp.immojump.de/mcp
# unit + annotation tests
PYTHONPATH=src pytest -q
```

Escalation if review stalls: `mcp-review@anthropic.com`.
