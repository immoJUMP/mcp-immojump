# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

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
