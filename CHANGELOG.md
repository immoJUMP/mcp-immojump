# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

## [Unreleased]
### Security
- OAuth: `/oauth/authorize` gibt Codes nur noch an Rücksprung-Adressen auf
  bekannten KI-Apps (ChatGPT, Claude, Cursor), Loopback und Origins aus
  `IMMOJUMP_MCP_OAUTH_REDIRECT_ORIGINS`. Vorher war für nicht selbst
  ausgestellte `client_id`s jede `redirect_uri` erlaubt.
- OAuth: PKCE mit `S256` ist Pflicht; Codes ohne Challenge werden nicht mehr
  ausgestellt oder eingetauscht.
- `/oauth/register` behält nur freigegebene `redirect_uris` und lehnt eine
  Registrierung ohne solche mit `invalid_redirect_uri` ab.
- Die Anmeldeseite nennt Loopback-Rücksprünge „ein Programm auf diesem Computer“.

### Fixed
- OAuth: `/oauth/token` gibt einen `refresh_token` aus und akzeptiert
  `grant_type=refresh_token`. Vorher meldete der Server `expires_in` 24 h ohne
  Refresh-Grant; ChatGPT musste sich täglich neu anmelden, geplante Aufgaben
  scheiterten mit „Token abgelaufen“. Braucht `IMMOJUMP_MCP_OAUTH_SECRET`.
- OAuth: Codes und Client-Registrierungen überleben Neustarts und Rolling
  Updates (versiegelt statt im Speicher).
- Abgelaufene OAuth-Access-Tokens bekommen `401 invalid_token`, damit der
  Client refresht.

### Changed
- Access- und Refresh-Tokens sind verschlüsselt; der API-Schlüssel steht nicht
  mehr im Klartext (base64) im Token. Alte Tokens gelten weiter.
- Anmeldeseite erklärt, dass Anlegen/Ändern einen Zugang „Lesen und ändern“
  braucht, warnt vor `ijr_`-Schlüsseln und nennt die Rücksprung-Domain.
- `403 READ_ONLY_TOKEN` im Tool-Ergebnis sagt, wie man einen Schreib-Zugang
  anlegt und die App neu verbindet.

## [0.1.0] - 2026-02-26
### Added
- Initial MCP server implementation for ImmoJUMP contacts orchestration.
- Tool surface:
  - `connection_test`
  - `contacts_import_preview`
  - `contacts_import_start`
  - `contacts_job_status`
  - `contacts_job_resume`
  - `contacts_job_cancel`
  - `contacts_duplicates_preview`
  - `contacts_merge_apply`
- Credential validation with base URL allowlist.
- HTTP client wrappers for unified import and merge endpoints.
- Basic unit tests for credential validation and request payload flow.
- CI workflow for linting and tests.
