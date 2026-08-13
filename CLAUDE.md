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
  validation.py        static ast.parse rejection of rule_code (M2)
  engine.py            restricted-namespace execution (M2)
  jobs/                RunComplianceRules and seed-data Jobs
  api/                 serializers.py, views.py, urls.py
  migrations/
  tests/
.github/workflows/     claude.yml (Lane B driver), test.yml (CI, added in M0)
build/                 create-nautobot-issues.sh (issue/milestone scaffolding)
docs/adr/              architecture decision records (M2 onward)
```

Touch only files named in the issue you are implementing or listed above. In
particular, do not edit `build/create-nautobot-issues.sh` or
`.github/workflows/claude.yml` unless the issue is explicitly about them.

**The map above is exhaustive — do not add modules that are not on it.**
Specifically, **do not create `admin.py`**. Nautobot surfaces models through
its own UI (views, tables, filters, navigation), which M4 delivers; a Django
admin registration is not part of this app and would sit unused. This has been
added and removed twice already — if a model feels like it needs admin
registration, it does not.

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

## Sandbox contract (M2) — decided, not open

The rule engine executes user-supplied Python. These decisions are **already
made**; implement them, do not re-derive or widen them. If an issue seems to
require deviating, stop and comment on the issue instead.

### Threat model

Rule authorship is restricted to trusted users holding the relevant Nautobot
RBAC permission. This is **defence in depth against mistakes and low-effort
mischief — not a hard security boundary** against a determined attacker with
rule-authoring rights. Say so plainly in the ADR and in module docstrings;
do not describe it as a sandbox that contains hostile code.

### Two layers

1. **Static** (`validation.py`) — `ast.parse` at `ComplianceRule` save time.
   Rejects before anything is persisted.
2. **Runtime** (`engine.py`) — `exec` against an explicitly built namespace.
   Never pass real `__builtins__`.

Layer 2 assumes layer 1 ran, but must not depend on it: a rule reaching the
engine unvalidated should still be contained.

### Static rejection rules (`validation.py`)

Reject rule_code containing any of:

- `Import` / `ImportFrom` nodes — any import at all
- A call to any of: `eval`, `exec`, `compile`, `__import__`, `open`,
  `globals`, `locals`, `vars`, `getattr`, `setattr`, `delattr`, `input`,
  `breakpoint`, `memoryview`
- Any `Attribute` node whose `attr` starts and ends with `__`
  (`__class__`, `__globals__`, `__subclasses__`, `__bases__`, …)
- Any `Name` referring to `os`, `sys`, `subprocess`, `shutil`, `socket`,
  `pathlib`, `importlib`, `builtins`

Raise `django.core.exceptions.ValidationError` naming what was rejected and
why. When in doubt, reject — a false rejection is a support ticket, a false
acceptance is an incident.

### Runtime namespace (`engine.py`)

Builtins allowlist — exactly these, nothing else:

```
len str int float bool isinstance any all sorted enumerate zip
min max sum abs round list dict set tuple range print
```

Modules: **`re` only**, pre-injected. Real compliance rules need pattern
matching and imports are banned, so `re` is provided directly. Do not inject
any other module; do not add one because a rule would be tidier with it.

### Rule signature convention

`rule_code` defines exactly one top-level function. The engine inspects its
signature and passes the subset of `configuration` / `commands` it declares,
as keyword arguments. A rule declaring neither is called with no arguments.

### Result mapping

| Outcome | Result |
|---|---|
| No exception | `status="pass"`, `output=""` |
| `AssertionError` | `status="fail"`, `output=str(exc)` |
| Any other exception | `status="error"`, `output=f"{type(exc).__name__}: {exc}"` |

### Honesty requirement

`validation.py` must carry a comment block listing bypasses this approach does
**not** catch. Document real limitations rather than implying completeness —
an overstated guarantee is worse than an acknowledged gap.

### Order

`#10` (ADR) → `#8` (validation) → `#9` (engine). The ADR records the decisions
above before code depends on them.

## Conventions

- Follow Nautobot App conventions: subclass Nautobot's base model/view/filter
  classes rather than plain Django ones where a Nautobot equivalent exists.
- Match the surrounding code's naming and comment density.
- Do not add dependencies not named in the issue.
