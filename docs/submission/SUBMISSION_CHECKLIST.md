# Anthropic Software Directory — Submission Checklist (TEMPLATE)

> Every box below marked `[?]` is a claim you need to **verify yourself**
> before submitting at <https://clau.de/mcp-directory-submission>. Claude
> Code cannot verify deployment specifics (TLS versions, proxy config,
> hosting provider). Boxes marked `[x]` are code-level facts verified in
> this repo.

Scope: remote MCP server. The `.mcpb` desktop bundle is **not** being
submitted.

---

## 1. Basic metadata (fill in)

| Field | Value |
|------|------|
| Connector name | `immoJUMP` |
| Tagline | CRM, pipelines & property operations for real-estate investors |
| Category | Productivity / CRM |
| Vendor | «TODO: legal entity» |
| Contact e-mail | «TODO» |
| Support e-mail | «TODO» |
| Public landing page | «TODO: stub in `LANDING_PAGE.md`» |
| Server URL (Streamable HTTP) | «TODO, e.g. https://mcp.immojump.de/mcp» |
| Server URL (SSE) | «TODO, e.g. https://mcp.immojump.de/sse» |
| OAuth metadata URL | «TODO»`/.well-known/oauth-protected-resource` |
| Privacy Policy URL | «TODO: stub in `PRIVACY_POLICY.md`» |
| Terms of Service URL | «TODO» |

## 2. Auth & transport (Review Criteria)

- [x] OAuth 2.1 with PKCE (S256) — `src/mcp_immojump/oauth.py`
- [x] Dynamic Client Registration (RFC 7591) — `/oauth/register`
- [x] Protected-resource metadata (RFC 9728) — `/.well-known/oauth-protected-resource`
- [x] Authorization-server metadata (RFC 8414) — `/.well-known/oauth-authorization-server`
- [x] Origin-Header validation on `/mcp`, `/sse`, `/messages` — `_OAuthFrontMiddleware`
- [x] `X-Frame-Options: DENY` on OAuth authorize page — `src/mcp_immojump/oauth.py`
- [x] No API keys in prompt — credentials exchanged via OAuth flow
- [x] Base URL allowlist in client — `ALLOWED_BASE_URLS` in `client.py`
- [?] HTTPS-only in production, TLS ≥ 1.2 — depends on edge / reverse-proxy config; **verify**
- [?] HSTS, CSP, Referrer-Policy at edge — **verify**

## 3. Tool design (Review Criteria)

- [x] Every tool carries either `readOnlyHint=True` or `destructiveHint` via `ToolAnnotations`
- [x] Coverage test enforces this: `tests/test_annotation_coverage.py`
- [x] No tool mixes GET + POST/PUT/DELETE semantics (each wraps a single client method)
- [x] All tool names ≤ 64 characters (longest: 34)
- [x] Descriptions contain no hidden / injection-style instructions
- [x] First-party only — all HTTP calls hit ImmoJUMP's own APIs

## 4. Content & policy

- [x] No money transfers
- [x] No cryptocurrency
- [x] No AI-generated media
- [?] Legitimate proprietor — confirm ImmoJUMP owns all consumed endpoints
- [ ] Acceptance of [Directory Policy](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy)
- [ ] Acceptance of [Directory Terms](https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms)

## 5. Deliverables uploaded in the form

- [ ] Public documentation URL
- [ ] Privacy Policy URL (template: `PRIVACY_POLICY.md`)
- [ ] Demo / test account credentials and setup instructions (template: `DEMO_ACCOUNT.md`)
- [ ] Logo assets — SVG + PNG at 512 × 512
- [ ] 2-3 short screenshots of the connector in use in claude.ai
- [ ] Optional: short walk-through video (< 2 min)

## 6. Pre-flight validation

```bash
# annotation + middleware + server unit tests
PYTHONPATH=src pytest -q
# lint
PYTHONPATH=src ruff check src tests
# live smoke test against your deployment
npx @modelcontextprotocol/inspector «TODO: live server URL»
```

Escalation if review stalls: `mcp-review@anthropic.com`.
