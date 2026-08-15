# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2026-08-15

### Added

- **Data models**: `ComplianceRule` (a named, severity-rated pytest-style rule),
  `ComplianceRuleSet` (a named group of rules), and `ComplianceTestResult` (the recorded
  pass/fail/error outcome of running one rule against one device).
- **Sandboxed rule execution**: `rule_code` is statically rejected at save time
  (`validation.py`, an `ast.parse()`-based check against imports, banned calls, dunder
  attribute access, and banned module names) and executed at run time against a
  restricted namespace (`engine.py`, a curated builtins allowlist plus the `re` module).
  Documented in [`docs/adr/0001-rule-sandboxing.md`](docs/adr/0001-rule-sandboxing.md).
- **`RunComplianceRules` Job**: runs a `ComplianceRuleSet`'s enabled rules against
  devices resolved from location/role/platform/tag filters, gathering each device's data
  from Golden Config's latest backup (preferred) or live over NAPALM (fallback), and
  records one `ComplianceTestResult` per rule x device.
- **UI**: list/detail/edit/delete views for `ComplianceRule` and `ComplianceRuleSet`; a
  filterable `ComplianceTestResult` results list (by device, rule, severity, status, and
  run-time range); a "Compliance" tab on the Device detail page; a fleet-wide Compliance
  Dashboard widget.
- **REST API**: full CRUD for `ComplianceRule`/`ComplianceRuleSet`; a read-only
  `ComplianceTestResult` endpoint with the same filters as the UI; a job-trigger endpoint
  so external callers (e.g. CI/CD pipelines) can enqueue a `RunComplianceRules` run
  without going through the UI, polling the returned `JobResult` for completion.
- **Example rules and seed data**: five example `ComplianceRule` definitions (login
  banner, NTP server, default SNMP community string, SSH-only management, unencrypted
  HTTP management server), loadable via the idempotent, optional "Load Example
  Compliance Rules (optional)" Job.
- **CI**: a GitHub Actions workflow running the test suite against Postgres and Redis
  service containers on every push to `master` and every pull request.
- Targets Nautobot 3.x.
