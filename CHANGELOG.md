# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

## [Unreleased]
### Added
- `units_create`/`units_update` nennen das Einheitenfeld `floor` (Etage):
  `UG`, `EG`, `1. OG` … `30. OG`, `DG`; übliche Schreibweisen wie
  „Erdgeschoss“, „1.OG“, „Souterrain“ normalisiert das Backend, `null` leert.
- `activity_template_create`/`activity_template_update` beschreiben
  `assignee_mode` (`fixed`, `role`, `actor` = „wer den Status ändert“) samt
  Ausweichregel; `assigned_to_id` ist eine Nutzer-ID (Zahl), keine UUID.

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
