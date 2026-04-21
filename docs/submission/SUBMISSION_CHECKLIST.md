# Anthropic Software Directory — Submission Checklist

> Boxes marked `[x]` are code-level facts verified in this repo. Boxes
> marked `[?]` require runtime / deployment verification. Fields still
> shown as `«TODO»` in §1 must be filled in by the vendor before the
> form is submitted at <https://clau.de/mcp-directory-submission>.

Scope: remote MCP server. The `.mcpb` desktop bundle is **not** being
submitted.

---

## 1. Basic metadata

| Field | Value |
|------|------|
| Connector name | `immoJUMP` |
| Tagline | CRM, pipelines & property operations for real-estate investors |
| Category | Productivity / CRM |
| Vendor | ImmoDigit GmbH (§5 TMG details: <https://immojump.de/ng/impressum>) |
| Contact e-mail | `info@immojump.de` |
| Support e-mail | `info@immojump.de` |
| Public landing page | <https://immojump.de> |
| Server URL (Streamable HTTP) | `https://mcp.immojump.de/mcp` |
| Server URL (SSE) | `https://mcp.immojump.de/sse` |
| OAuth metadata URL | `https://mcp.immojump.de/.well-known/oauth-protected-resource` |
| Privacy Policy URL | «TODO: public URL, e.g. https://immojump.de/legal/privacy-mcp» |
| Terms of Service URL | «TODO: public URL» |

## 2. Auth & transport (Review Criteria)

- [x] OAuth 2.1 with PKCE (S256) — `src/mcp_immojump/oauth.py`
- [x] Dynamic Client Registration (RFC 7591) — `/oauth/register`
- [x] Protected-resource metadata (RFC 9728) — `/.well-known/oauth-protected-resource`
- [x] Authorization-server metadata (RFC 8414) — `/.well-known/oauth-authorization-server`
- [x] Origin-Header validation on `/mcp`, `/sse`, `/messages` — `_OAuthFrontMiddleware`
- [x] `X-Frame-Options: DENY` on OAuth authorize page — `src/mcp_immojump/oauth.py`
- [x] No API keys in prompt — credentials exchanged via OAuth flow
- [x] Base URL allowlist in client — `ALLOWED_BASE_URLS` in `client.py`
- [x] HTTPS-only in production, TLS ≥ 1.2 — verified against `mcp.immojump.de` 2026-04-21 (1.0/1.1 rejected, 1.2 + 1.3 accepted)
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
- [x] Logo — `docs/submission/branding/logo-512.png` (512 × 512 PNG); SVG vector still pending
- [ ] 2-3 short screenshots of the connector in use in claude.ai
- [ ] Optional: short walk-through video (< 2 min)

## 6. Pre-flight validation

```bash
# annotation + middleware + server unit tests
PYTHONPATH=src pytest -q
# lint
PYTHONPATH=src ruff check src tests
# live smoke test against production
npx @modelcontextprotocol/inspector https://mcp.immojump.de/mcp
# Origin rejection sanity check
curl -i -H "Origin: https://evil.example.com" https://mcp.immojump.de/mcp   # expect 403
# Clickjack-defence sanity check
curl -sI "https://mcp.immojump.de/oauth/authorize?client_id=x&redirect_uri=https://claude.ai/cb&state=s&code_challenge=c&code_challenge_method=S256" | grep -i x-frame-options   # expect "DENY"
```

Escalation if review stalls: `mcp-review@anthropic.com`.
