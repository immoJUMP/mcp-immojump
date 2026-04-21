# Submission package — Anthropic Software Directory

This folder bundles everything a reviewer or the submitting engineer needs
when filling out the Remote MCP Server form at
<https://clau.de/mcp-directory-submission>.

| File | Purpose |
|------|---------|
| `SUBMISSION_CHECKLIST.md` | Single source of truth for the form fields, plus review-criteria sign-off |
| `PRIVACY_POLICY.md` | Template for the public Privacy Policy URL |
| `DEMO_ACCOUNT.md` | Test-account credentials, seed-data recipe, reviewer prompts |
| `LANDING_PAGE.md` | Copy for the public `/mcp` landing page |
| `branding/` | Logo + screenshot assets (populate before submitting) |

## What still has to happen manually

Anthropic's directory is self-serve but the form itself is a manual web flow
— it requires human input for the test-account password, the uploaded
branding assets, and the policy acceptance checkboxes. Claude Code cannot
submit it. Use this folder as the launchpad, then open
<https://clau.de/mcp-directory-submission> to finish.

Queue time varies; escalate to `mcp-review@anthropic.com` only after 10
business days.
