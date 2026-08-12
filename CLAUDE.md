# CLAUDE.md

Conventions for the `nautobot-app-pytest-compliance-rule-engine` build.

## What this is

A Nautobot App providing a pytest-style compliance rule engine: users define
compliance rules as small Python snippets, and a Nautobot Job executes them
against device data and records pass/fail results.

- **Repo**: `nautobot-app-pytest-compliance-rule-engine`
- **App / distribution name**: `nautobot-pytest-compliance-rule-engine`
- **Python package**: `nautobot_pytest_compliance_rule_engine`
- **Default branch**: `master`

Use those names exactly. Do not shorten the package to
`nautobot_pytest_compliance`.

## Repo map

The target layout (created incrementally by the M0/M1 issues):

```
nautobot_pytest_compliance_rule_engine/
  __init__.py          NautobotAppConfig subclass
  models.py            ComplianceRule, ComplianceTestResult, ComplianceRuleSet
  views.py  tables.py  filters.py  forms.py  urls.py
  navigation.py        nav menu items
  template_content.py  device detail tab injection
  engine/              static validation + restricted execution (M2)
  jobs/                RunComplianceRules and seed-data Jobs
  api/                 serializers.py, views.py, urls.py
  migrations/
  tests/
.github/workflows/     claude.yml (Lane B driver), test.yml (CI, added in M0)
build/                 create-nautobot-issues.sh (issue/milestone scaffolding)
```

Touch only files named in the issue you are implementing or listed above. In
particular, do not edit `build/create-nautobot-issues.sh` or
`.github/workflows/claude.yml` unless the issue is explicitly about them.

## Milestones

Issues are grouped M0–M8 and are ordered by dependency. If your issue depends
on work from an earlier milestone that is not merged yet, post one clarifying
comment on the issue rather than stubbing the missing piece.

## Definition of done

An issue is done when all of these hold:

1. The acceptance criteria in the issue body are met.
2. New behaviour has tests under
   `nautobot_pytest_compliance_rule_engine/tests/`.
3. Model changes ship with their migration (`nautobot-server makemigrations`),
   committed alongside the model change.
4. Lint and tests are clean (see below).
5. The PR description states what was verified and what was not.

## Checks

Run what exists; early milestones are still scaffolding this tooling. Do not
invent a workaround if a target is genuinely absent — say so in the PR.

```
ruff check .
black --check .
nautobot-server test nautobot_pytest_compliance_rule_engine
```

## Security constraint (M2)

The rule engine executes user-supplied Python. This is the sensitive part of
the build and the reason those issues are `lane:interactive` — do not widen
the sandbox on your own initiative.

- Rule code is validated with `ast.parse` and rejected on disallowed nodes
  (imports, attribute access to dunders, `exec`/`eval`, comprehension-based
  escapes) *before* execution.
- Execution uses an explicitly constructed restricted namespace. Never pass
  real `__builtins__`.
- No filesystem, network, or subprocess access from rule code.

If an issue seems to require relaxing any of the above, stop and comment on
the issue instead.

## Conventions

- Follow Nautobot App conventions: subclass Nautobot's base model/view/filter
  classes rather than plain Django ones where a Nautobot equivalent exists.
- Match the surrounding code's naming and comment density.
- Do not add dependencies not named in the issue.
