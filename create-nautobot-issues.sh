#!/usr/bin/env bash
#
# create-nautobot-issues.sh
#
# Creates all 30 GitHub issues for the nautobot-pytest-compliance build,
# with correct labels, in a target repo.
#
# Usage:
#   ./create-nautobot-issues.sh OWNER/REPO
#
# Requires: gh CLI authenticated (gh auth login), repo already created.
#
# Labels used: claude-go, milestone:M0..M8, lane:unattended,
# lane:interactive, lane:manual, model:opus, manual
#
# This script ensures all labels exist first (gh label create is
# idempotent-safe via --force), then creates each issue with its title,
# body (from a heredoc), and labels.

set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 OWNER/REPO"
  exit 1
fi

REPO="$1"

echo "==> Ensuring labels exist in $REPO"

declare -a LABELS=(
  "claude-go:1f883d:Triggers unattended Lane B pipeline"
  "milestone:M0:5319e7:Repo scaffolding & CI foundation"
  "milestone:M1:5319e7:Data models"
  "milestone:M2:d73a4a:Sandboxed rule execution engine"
  "milestone:M3:5319e7:Job execution & device data gathering"
  "milestone:M4:5319e7:Views & UI"
  "milestone:M5:5319e7:REST API"
  "milestone:M6:5319e7:Example rules & seed data"
  "milestone:M7:5319e7:Documentation & release"
  "milestone:M8:fbca04:Stretch — live device validation"
  "lane:unattended:0e8a16:Runs via claude-go Lane B pipeline"
  "lane:interactive:1d76db:Recommended to drive interactively (Lane A)"
  "lane:manual:e4e669:No Claude Code — manual task"
  "model:opus:d93f0b:Escalate to Claude Opus 5 instead of Sonnet 5 default"
  "manual:e4e669:Manual task, not for automation"
)

for entry in "${LABELS[@]}"; do
  IFS=':' read -r name color desc <<< "$entry"
  gh label create "$name" --repo "$REPO" --color "$color" --description "$desc" --force 2>/dev/null || true
done

echo "==> Labels ready. Creating issues..."

create_issue() {
  local title="$1"
  local labels="$2"
  local body="$3"
  echo "Creating: $title"
  gh issue create --repo "$REPO" --title "$title" --label "$labels" --body "$body"
}

# ---------------------------------------------------------------------------
# M0 — Scaffolding & CI Foundation
# ---------------------------------------------------------------------------

create_issue "M0: Scaffold nautobot-pytest-compliance app structure" \
  "claude-go,milestone:M0,lane:unattended" \
  "$(cat <<'EOF'
Scaffold a new Nautobot App called `nautobot-pytest-compliance` using the
standard Nautobot App cookiecutter/structure (see
https://docs.nautobot.com/projects/core/en/stable/apps/api/).

Create:
- Standard package layout: nautobot_pytest_compliance/{models.py, views.py,
  tables.py, filters.py, forms.py, urls.py, navigation.py, template_content.py,
  api/{serializers.py, views.py, urls.py}, migrations/, jobs/, tests/}
- NautobotAppConfig subclass in __init__.py registering the app (name,
  verbose_name, description, version, author, required_settings if any)
- pyproject.toml with poetry/setuptools metadata, Nautobot as a dependency
- .gitignore appropriate for a Python/Django/Nautobot project

Do not implement any models or business logic yet — this issue is scaffolding
only. Confirm the app installs cleanly into a bare Nautobot instance
(nautobot-server should list it under installed apps) before completing.
EOF
)"

create_issue "M0: GitHub Actions CI workflow with Postgres/Redis service containers" \
  "claude-go,milestone:M0,lane:unattended" \
  "$(cat <<'EOF'
Add a GitHub Actions workflow (.github/workflows/test.yml) that:
- Spins up Postgres 16 and Redis 7 as service containers
- Installs Python 3.12, Nautobot, and this app's dependencies
- Runs `nautobot-server migrate` against the service containers
- Runs `nautobot-server test nautobot_pytest_compliance`
- Triggers on push and pull_request

At this stage the app has no models/tests yet, so the test run should pass
trivially (0 tests collected, exit 0). The goal of this issue is a GREEN CI
pipeline on an empty app — later issues will add real tests to it.

Reference nautobot/nautobot's own GitHub Actions workflows for the service
container pattern if you need an example.
EOF
)"

create_issue "M0: Packaging, lint config, and pre-commit hooks" \
  "claude-go,milestone:M0,lane:unattended" \
  "$(cat <<'EOF'
Finalize packaging and code quality tooling for nautobot-pytest-compliance:
- Complete pyproject.toml (build system, dependencies, dev-dependencies:
  pytest, black, ruff)
- Add .pre-commit-config.yaml with black and ruff hooks
- Add a README.md stub (title, one-line description, "Installation" and
  "Usage" section headers only — full content comes in M7)

Verify `pip install -e .` succeeds locally in a clean virtualenv.
EOF
)"

# ---------------------------------------------------------------------------
# M1 — Data Models
# ---------------------------------------------------------------------------

create_issue "M1: ComplianceRule model" \
  "claude-go,milestone:M1,lane:unattended" \
  "$(cat <<'EOF'
Add a ComplianceRule model to nautobot_pytest_compliance/models.py:

Fields:
- name (CharField, unique)
- description (TextField, blank=True)
- severity (CharField with choices: low, medium, high — mirror Netpicker's
  @low/@medium/@high pattern)
- platform (ForeignKey to nautobot.dcim.models.Platform, null=True, blank=True
  — null means "applies to all platforms")
- rule_code (TextField — stores the Python/pytest function body as text)
- enabled (BooleanField, default=True)
- tags (Nautobot's TagsField, from nautobot.extras.models)

Inherit from Nautobot's PrimaryModel (or the appropriate base class per
current Nautobot conventions) so it gets change-logging, custom fields, and
relationships for free. Register in admin.py. Create the migration.

Write unit tests: model creation, __str__ returns name, severity choices are
enforced, unique constraint on name.
EOF
)"

create_issue "M1: ComplianceTestResult model" \
  "claude-go,milestone:M1,lane:unattended" \
  "$(cat <<'EOF'
Add a ComplianceTestResult model to nautobot_pytest_compliance/models.py:

Fields:
- rule (ForeignKey to ComplianceRule, on_delete=CASCADE)
- device (ForeignKey to nautobot.dcim.models.Device, on_delete=CASCADE)
- status (CharField with choices: pass, fail, error)
- output (TextField, blank=True — captures assertion message or error trace)
- run_datetime (DateTimeField, auto_now_add=True)
- job_result (ForeignKey to nautobot.extras.models.JobResult, null=True,
  blank=True, on_delete=SET_NULL)

This model should be read-mostly (created by the Job in M3, not manually
edited via UI forms). Register in admin.py as read-only. Create the
migration.

Write unit tests: model creation, status choices enforced, FK relationships
resolve correctly, ordering (most recent run_datetime first).
EOF
)"

create_issue "M1: ComplianceRuleSet model" \
  "claude-go,milestone:M1,lane:unattended" \
  "$(cat <<'EOF'
Add a ComplianceRuleSet model to nautobot_pytest_compliance/models.py:

Fields:
- name (CharField, unique)
- description (TextField, blank=True)
- rules (ManyToManyField to ComplianceRule, related_name="rule_sets")

Purpose: lets users group rules (e.g. "CIS Cisco IOS Hardening") and assign
the whole set to a Job run rather than picking individual rules each time.

Inherit from PrimaryModel per Nautobot conventions. Register in admin.py.
Create the migration.

Write unit tests: model creation, M2M relationship add/remove, __str__
returns name.
EOF
)"

create_issue "M1: Model layer test coverage review" \
  "claude-go,milestone:M1,lane:unattended" \
  "$(cat <<'EOF'
Review all three models added in the prior M1 issues together. Add any
missing test coverage:
- Cascade delete behavior (deleting a ComplianceRule should cascade-delete
  its ComplianceTestResults; deleting a Device should cascade-delete its
  ComplianceTestResults)
- ComplianceRuleSet with zero rules is valid
- Querying ComplianceTestResult filtered by rule severity (via the FK)

Confirm `nautobot-server test nautobot_pytest_compliance` passes fully in
CI (this is the first issue where the M0 CI pipeline should show real test
counts, not zero).
EOF
)"

# ---------------------------------------------------------------------------
# M2 — Sandboxed Rule Execution Engine (highest risk — model:opus, interactive)
# ---------------------------------------------------------------------------

create_issue "M2: Static validation (ast.parse) for rule_code safety" \
  "claude-go,milestone:M2,model:opus,lane:interactive" \
  "$(cat <<'EOF'
Add a validation function (nautobot_pytest_compliance/validation.py) that
runs at ComplianceRule save-time (override clean() or save()) to statically
reject unsafe rule_code before it's ever persisted or executed.

Using Python's ast module, parse the rule_code string and reject it if it
contains:
- Any import statement (import, from...import) — rules should not import
  anything; all context they need is passed as function arguments
- Calls to eval, exec, compile, __import__, open, os.*, subprocess.*, sys.*
- Access to dunder attributes (__class__, __globals__, __builtins__, etc.)
- Any attribute access chain that could reach outside the sandbox (walk the
  AST for Attribute nodes and flag suspicious chains)

On rejection, raise Django's ValidationError with a clear message pointing
at what was rejected.

Write unit tests with adversarial rule_code samples — at minimum, test that
each of the following is rejected: "import os", "eval('1+1')",
"__import__('os').system('ls')", "().__class__.__bases__[0]" (sandbox escape
attempt), and confirm a legitimate rule (assert 'keyword' in configuration)
is accepted.

This is the highest-risk part of the app since it's the gate for
user-submitted code execution. Be conservative — when in doubt, reject.
Document any bypass techniques you're aware of that this approach does NOT
catch (be honest about limitations) in a comment block at the top of
validation.py.
EOF
)"

create_issue "M2: Restricted-namespace execution engine" \
  "claude-go,milestone:M2,model:opus,lane:interactive" \
  "$(cat <<'EOF'
Add an execution engine (nautobot_pytest_compliance/engine.py) that takes a
validated ComplianceRule (already passed the static ast.parse() check) plus
a `configuration` string and/or `commands` dict, and executes the rule_code
in a restricted namespace.

Approach:
- Build the function from rule_code using exec() with a restricted globals
  dict — no __builtins__ except a minimal safe allowlist (len, str, int,
  bool, isinstance, etc. — NOT open, __import__, eval)
- Call the resulting function with `configuration` and/or `commands` as
  keyword arguments, matching whatever the rule's signature expects
- Catch AssertionError -> return (status="fail", output=str(exception))
- Catch any other Exception -> return (status="error", output=str(exception)
  + type name)
- No exception -> return (status="pass", output="")

Write unit tests covering: a passing rule, a failing rule (assert message is
captured correctly in output), a rule that raises a non-assertion exception
(e.g. KeyError from bad input), and confirm the restricted namespace
actually blocks a rule that somehow got past the static check but attempts
a runtime sandbox escape (defense in depth).

Reference Netpicker's rule syntax pattern for the function signature
convention: https://netpicker.io/knowledge-base/test-rule-syntax/
EOF
)"

create_issue "M2: Sandboxing design doc / ADR" \
  "claude-go,milestone:M2,lane:interactive" \
  "$(cat <<'EOF'
Before the execution engine issue is merged, write a design doc
(docs/adr/0001-rule-sandboxing.md, following an Architecture Decision Record
format) covering:

1. Context: why user-submitted Python needs to be executed at all (the
   pytest-style compliance rule model), and why this is inherently risky
2. Decision: the two-layer approach (static ast.parse() rejection, plus
   restricted-namespace exec())
3. Known limitations: be explicit about what this approach does NOT
   protect against (this is not a true sandbox like a subprocess/
   container-based approach; assumes rule_code authorship is restricted to
   trusted, permissioned users via Nautobot's RBAC, not arbitrary input)
4. Alternatives considered and rejected (e.g. subprocess with resource
   limits, RestrictedPython library) and why the simpler approach was
   chosen for v1
5. Recommendation: gate ComplianceRule creation/edit permissions tightly in
   Nautobot's RBAC

This doc should exist before the execution engine PR is approved.
EOF
)"

# ---------------------------------------------------------------------------
# M3 — Job Execution & Device Data Gathering
# ---------------------------------------------------------------------------

create_issue "M3: RunComplianceRules Job — input form" \
  "claude-go,milestone:M3,lane:unattended" \
  "$(cat <<'EOF'
Create a Nautobot Job (nautobot_pytest_compliance/jobs/run_compliance.py)
called RunComplianceRules with an input form (using Nautobot's Job
variables/ScriptVariable pattern) that accepts:
- device_queryset filters: site, role, platform, tag (use Nautobot's
  standard MultiObjectVar patterns for each)
- rule_set: a ComplianceRuleSet selector (ObjectVar)

The Job's run() method can be a stub for this issue (just log the resolved
device queryset and selected rule set) — the actual execution logic comes
in a later issue.

Register the Job so it appears in Nautobot's Jobs UI. Write a test
confirming the Job form validates and resolves the correct device queryset
given sample filter inputs.
EOF
)"

create_issue "M3: Optional Golden Config integration" \
  "claude-go,milestone:M3,lane:unattended" \
  "$(cat <<'EOF'
Add a helper function (nautobot_pytest_compliance/integrations/golden_config.py)
that, given a Device, attempts to pull its latest backed-up configuration
from the Golden Config app (nautobot-plugin-golden-config) if that app is
installed.

Requirements:
- Detect at runtime whether golden_config is in Nautobot's installed apps
  (don't hard-require it as a dependency)
- If installed, query its GoldenConfig/ConfigCompliance models (check the
  current Golden Config app's API/model names) for the device's latest
  backup config content
- If not installed, or no backup exists for the device, return None and
  log a clear message — the caller should be able to fall back gracefully
  to live device data gathering instead

Write unit tests mocking both the "golden config installed with data" and
"golden config not installed" cases.
EOF
)"

create_issue "M3: Live device data gathering (NAPALM/Netmiko)" \
  "claude-go,milestone:M3,lane:unattended" \
  "$(cat <<'EOF'
Add a helper function (nautobot_pytest_compliance/integrations/live_device.py)
that, given a Device with valid Nautobot-stored credentials/secrets, gathers
a `commands` dict of live show-command output using NAPALM or Netmiko
(match whichever library convention is already used elsewhere in similar
Nautobot apps — check nautobot-plugin-device-onboarding for the pattern
Nautobot commonly uses).

This function should accept a list of command strings to run (rules may
each need different commands) and return {command: output_text}.

IMPORTANT: this issue must NOT attempt to connect to real devices in CI —
GitHub Actions runners have no network path to real network hardware. Use
mocking (unittest.mock or pytest fixtures with canned output) for all tests
in this issue. Live device testing happens separately in M8, on
infrastructure that actually has network access (WSL/containerlab).

Write unit tests using mocked NAPALM/Netmiko connections confirming the
function correctly builds and returns the commands dict.
EOF
)"

create_issue "M3: Wire execution engine into the Job" \
  "claude-go,milestone:M3,model:opus,lane:unattended" \
  "$(cat <<'EOF'
Complete the RunComplianceRules Job's run() method by wiring together:
- The resolved device queryset and rule_set from the input form issue
- Config/command data gathering: try Golden Config first, fall back to live
  device data if unavailable, skip the device with a logged warning if
  neither is available
- For each device x rule combination in the rule_set, call the execution
  engine with the gathered configuration/commands data
- Persist a ComplianceTestResult for each device x rule run, linked to this
  JobResult

Handle partial failures gracefully — if one device's data gathering fails,
log it and continue with the remaining devices rather than aborting the
whole Job run.

Write integration tests using mocked device data (no real Golden Config
instance or live device needed) covering: a full run across multiple
devices and rules with mixed pass/fail results, a device with no available
data (should skip and log, not crash), and confirm ComplianceTestResult
rows are created correctly with the right JobResult FK.

This issue integrates several prior pieces — review each of their
interfaces before starting, and flag in the PR description if any
interface needs adjusting to fit together cleanly.
EOF
)"

create_issue "M3: End-to-end Job integration test suite" \
  "claude-go,milestone:M3,lane:unattended" \
  "$(cat <<'EOF'
Add a comprehensive integration test suite (tests/test_job_integration.py)
that exercises the full RunComplianceRules Job end-to-end using Nautobot's
Job testing utilities (run_job_for_testing or equivalent per current
Nautobot conventions), entirely with mocked device data — no live
connections.

Cover: a rule_set with rules of mixed severity across multiple devices,
confirming correct pass/fail/error counts; a device matching zero rules in
the set (edge case); a rule_set with zero rules (edge case, should complete
with zero results, not error).

Confirm nautobot-server test nautobot_pytest_compliance passes fully in the
GitHub Actions CI pipeline (Postgres/Redis service containers from M0).
EOF
)"

# ---------------------------------------------------------------------------
# M4 — Views & UI
# ---------------------------------------------------------------------------

create_issue "M4: List/detail/edit/delete views for ComplianceRule and ComplianceRuleSet" \
  "claude-go,milestone:M4,lane:unattended" \
  "$(cat <<'EOF'
Add standard Nautobot UI views for ComplianceRule and ComplianceRuleSet
following Nautobot's generic view pattern (ObjectListView, ObjectView,
ObjectEditView, ObjectDeleteView, ObjectBulkDeleteView) — reference any
existing Nautobot core app (e.g. dcim) for the exact pattern currently in
use.

Include:
- forms.py: ModelForm for each, with rule_code rendered as a textarea with
  a monospace font (add appropriate CSS class)
- tables.py: django-tables2 Table classes for list views, showing name,
  severity (ComplianceRule) or rule count (ComplianceRuleSet), enabled
  status, last modified
- filters.py: FilterSet classes supporting filtering by severity, platform,
  enabled status
- urls.py and navigation.py entries so these appear in Nautobot's nav menu
  under an appropriate section

Write tests confirming each view renders successfully (200 status) for a
superuser, and that permission-restricted users get appropriate 403s per
Nautobot's RBAC.
EOF
)"

create_issue "M4: Filterable ComplianceTestResult results table" \
  "claude-go,milestone:M4,lane:unattended" \
  "$(cat <<'EOF'
Add a read-only list view for ComplianceTestResult (no edit/delete — these
are system-generated) with:
- tables.py: Table showing device, rule (with severity badge), status
  (color-coded: green=pass, red=fail, orange=error), run_datetime,
  truncated output with a "view full" expand
- filters.py: FilterSet supporting filtering by device, rule, severity
  (via rule FK), status, and run_datetime range
- A URL and nav menu entry ("Compliance Results")

Write tests confirming the view renders, filters correctly narrow the
result set, and a non-privileged user without view permission gets a 403.
EOF
)"

create_issue "M4: Device detail page tab injection" \
  "claude-go,milestone:M4,lane:unattended" \
  "$(cat <<'EOF'
Use Nautobot's template_content.py extension mechanism to inject a new tab
("Compliance") onto the Device detail page, showing that device's most
recent ComplianceTestResult rows (reuse the table component from the
results-table issue, filtered to this device, limited to e.g. the last 20
results or last run).

Reference Nautobot's App template extension docs
(https://docs.nautobot.com/projects/core/en/stable/apps/api/) for the exact
hook pattern (TemplateExtension subclass, right_page/left_page/etc.).

Write a test confirming a device with existing ComplianceTestResults shows
the tab with correct content, and a device with none shows an appropriate
empty state (not an error).
EOF
)"

create_issue "M4: Dashboard summary widget" \
  "claude-go,milestone:M4,lane:unattended" \
  "$(cat <<'EOF'
Add a dashboard view/widget summarizing compliance state across the whole
fleet:
- Pass/fail/error counts by severity (low/medium/high), current snapshot
- A 30-day trend chart (use Chart.js — check what's already bundled with
  Nautobot's UI framework rather than adding a new JS dependency) showing
  daily pass/fail counts

This can be a standalone page (e.g. /plugins/pytest-compliance/dashboard/)
linked from the nav menu, or a template_content injection onto Nautobot's
existing home dashboard — pick whichever fits Nautobot's current app
conventions better and note which you chose in the PR description.

Write a test confirming the dashboard view renders successfully with both
empty data (no results yet) and populated data.
EOF
)"

# ---------------------------------------------------------------------------
# M5 — REST API
# ---------------------------------------------------------------------------

create_issue "M5: REST API — ComplianceRule and ComplianceRuleSet CRUD" \
  "claude-go,milestone:M5,lane:unattended" \
  "$(cat <<'EOF'
Add REST API serializers and ViewSets (api/serializers.py, api/views.py,
api/urls.py) for full CRUD on ComplianceRule and ComplianceRuleSet,
following Nautobot's standard API app pattern (NautobotModelSerializer,
NautobotModelViewSet or current equivalents).

Ensure the API respects the same RBAC permissions as the UI views from M4 —
no separate/looser permission model for the API.

Write API tests (using Nautobot's APITestCase or equivalent) covering
create/read/update/delete for both models, and a permission-denied case
for a user without the right role.
EOF
)"

create_issue "M5: Read-only ComplianceTestResult API endpoint" \
  "claude-go,milestone:M5,lane:unattended" \
  "$(cat <<'EOF'
Add a read-only REST API endpoint for ComplianceTestResult (list + detail,
no create/update/delete since these are system-generated) with filtering
support matching the UI filters from M4 (device, rule, severity, status,
date range) exposed as query parameters.

Write API tests confirming list/detail retrieval, filter query params work
correctly, and write attempts (POST/PUT/DELETE) return 405 Method Not
Allowed.
EOF
)"

create_issue "M5: Job trigger API endpoint" \
  "claude-go,milestone:M5,lane:unattended" \
  "$(cat <<'EOF'
Add a POST endpoint (e.g. /api/plugins/pytest-compliance/run/) that accepts
the same inputs as the RunComplianceRules Job form (device filters,
rule_set) and triggers the Job programmatically via Nautobot's Job
execution API (JobResult creation, enqueue mechanism — check current
Nautobot conventions for triggering Jobs from custom API views).

This endpoint exists specifically so external CI/CD pipelines (e.g. a
GitHub Actions workflow in a device-config repo) can trigger compliance
runs without going through the Nautobot UI.

Return the JobResult ID/URL so the caller can poll for completion status
via Nautobot's existing JobResult API.

Write a test confirming a valid POST triggers a JobResult and returns 202
Accepted with the expected payload shape.
EOF
)"

create_issue "M5: API integration test suite" \
  "claude-go,milestone:M5,lane:unattended" \
  "$(cat <<'EOF'
Review the full M5 API surface together and add any missing integration
test coverage — particularly: an end-to-end API flow (create a
ComplianceRule via API, create a ComplianceRuleSet containing it via API,
trigger a run via the Job trigger endpoint using mocked device data, poll
JobResult, then confirm ComplianceTestResult rows are retrievable via the
read-only endpoint).

Confirm full CI pipeline (nautobot-server test) passes with all API tests
included.
EOF
)"

# ---------------------------------------------------------------------------
# M6 — Example Rules & Seed Data
# ---------------------------------------------------------------------------

create_issue "M6: Example ComplianceRule fixtures" \
  "claude-go,milestone:M6,lane:unattended" \
  "$(cat <<'EOF'
Create 3-5 example ComplianceRule fixture entries (as a Django fixture JSON
file or a data migration, whichever fits Nautobot app conventions better)
matching Netpicker's example rule style
(https://github.com/netpicker/pytests-for-networking/blob/main/EXAMPLES.md):

1. Banner text check (assert expected banner string present in config)
2. NTP server configured (assert at least one ntp server line present)
3. SNMP community string is not "public" or "private" (assert these
   default strings are absent)
4. SSH-only management (assert telnet is not enabled / SSH is enabled)
5. (Optional) A CVE-style example: assert a known-vulnerable feature/command
   string is absent, matching the pattern from Netpicker's Cisco CVE blog
   post — reference the pattern only, do not reproduce their exact rule
   text verbatim; write an original equivalent

Each example should have realistic severity levels (low/medium/high) and a
clear description explaining what it checks and why it matters.
EOF
)"

create_issue "M6: Seed data loading Job" \
  "claude-go,milestone:M6,lane:unattended" \
  "$(cat <<'EOF'
Add a Job (jobs/load_example_rules.py) that loads the example
ComplianceRule fixtures into the database, for users who want to try the
app out immediately after install rather than writing rules from scratch.

This should be idempotent (running it twice shouldn't create duplicates —
use get_or_create keyed on rule name) and clearly labeled in the Jobs UI as
"Load Example Compliance Rules (optional)".

Write a test confirming it creates the expected rules on first run and
doesn't duplicate them on a second run.
EOF
)"

# ---------------------------------------------------------------------------
# M7 — Documentation & Release
# ---------------------------------------------------------------------------

create_issue "M7: README and documentation" \
  "claude-go,milestone:M7,lane:unattended" \
  "$(cat <<'EOF'
Complete README.md with:
- One-paragraph description of what the app does and why (reference the
  gap it fills vs Nautobot's existing Golden Config app — this does
  free-form pytest-style assertions against live/backed-up device state,
  not just intended-vs-actual config diffing)
- Installation instructions (pip install, add to PLUGINS in
  nautobot_config.py, run migrations)
- Configuration section (any required settings)
- "How to write a ComplianceRule" guide with a worked example, including
  what arguments the rule function receives (configuration, commands) and
  what's off-limits per the sandboxing constraints (no imports, no
  os/subprocess/eval access)
- Screenshot placeholders (mark clearly as TODO — actual screenshots need
  a live instance, add a note that these should be captured manually after
  WSL install)
- License section matching whatever license your other repos use

Also add docstrings to any public functions/classes still missing them
across the codebase (quick review pass).
EOF
)"

create_issue "M7: Changelog and release tagging" \
  "claude-go,milestone:M7,lane:unattended" \
  "$(cat <<'EOF'
Add a CHANGELOG.md following Keep a Changelog format, summarizing the
features delivered across M0-M7 as a v0.1.0 entry (data models, sandboxed
execution engine, Job, UI views, REST API, example rules).

Bump version in pyproject.toml to 0.1.0. Prepare (but do not push, unless
your workflow permissions allow it) a git tag v0.1.0 and note the exact
command to run in the PR description for manual execution.
EOF
)"

create_issue "M7 (Manual): Install into WSL Nautobot instance" \
  "manual,lane:manual" \
  "$(cat <<'EOF'
NOT for unattended pipeline — this is a manual task for you (Mick) to
perform once the v0.1.0 release is tagged:

1. pip install the release (or `pip install -e .` from a local clone) into
   your WSL2 ubuntu24-claude Nautobot instance
2. Add nautobot_pytest_compliance to PLUGINS in nautobot_config.py
3. Run migrations
4. Run the "Load Example Compliance Rules" Job to seed test data
5. Manually verify: UI views render, device tab shows results after running
   RunComplianceRules against a test device/containerlab node, API
   endpoints respond correctly
6. Capture the screenshots flagged as TODO in the README issue

No Claude Code prompt needed for this issue — it's a manual verification
checklist.
EOF
)"

# ---------------------------------------------------------------------------
# M8 — Stretch: Live Device Validation
# ---------------------------------------------------------------------------

create_issue "M8 (Stretch): containerlab live validation harness" \
  "claude-go,milestone:M8,model:opus,lane:interactive" \
  "$(cat <<'EOF'
Build a containerlab-based integration test harness (reuse patterns from
your existing frr01 or cve-demo containerlab projects) that stands up a
small topology (e.g. 2-3 FRR routers) and runs RunComplianceRules against
them via live NAPALM/Netmiko connections (not mocked — this is where the
real connection code actually gets exercised).

This CANNOT run on GitHub-hosted runners (no network path to a live
topology). Design this to run either:
(a) On your WSL2 environment directly, invoked manually or via a Makefile
    target, or
(b) On a self-hosted GitHub Actions runner registered on your WSL/home-lab
    infrastructure, if you want it in a workflow

Include a small set of example rules exercised against the containerlab
topology's real (not mocked) config/command output, confirming the full
pipeline works end-to-end against live devices.

Document the setup/teardown steps clearly since this harness has
infrastructure dependencies (containerlab, Docker) that CI doesn't have.
EOF
)"

create_issue "M8 (Stretch): Document self-hosted runner requirement" \
  "claude-go,milestone:M8,lane:unattended" \
  "$(cat <<'EOF'
Add a docs/live-validation.md explaining clearly:
- Why the containerlab harness can't run on GitHub-hosted runners (no
  network access to live/simulated devices)
- Two paths forward if you want this automated rather than manual: (a)
  register a self-hosted GitHub Actions runner on your WSL2 environment
  with containerlab installed, or (b) keep it as a manual pre-release
  verification step
- Link back to the main build plan's GitHub-only feasibility table for the
  full breakdown of what does/doesn't need self-hosted infrastructure

This is documentation only — no code changes.
EOF
)"

echo "==> Done. Created 30 issues in $REPO."
echo "==> Review the milestone:M2 and milestone:M8 issues (labeled lane:interactive) —"
echo "    these are recommended to drive yourself via Lane A rather than the claude-go pipeline."
