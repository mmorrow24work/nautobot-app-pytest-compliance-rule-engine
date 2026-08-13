# 1. Rule execution sandboxing

## Status

Accepted

## Context

`nautobot-pytest-compliance-rule-engine` lets users author compliance rules
as small, pytest-style Python functions (`ComplianceRule.rule_code`). A rule
is a plain Python function that receives a device's `configuration` and/or
`commands` output and asserts on it, e.g.:

```python
def check_ntp_configured(configuration):
    assert "ntp server" in configuration
```

The `RunComplianceRules` Job (M3) loads every enabled `ComplianceRule`,
executes its `rule_code` against real device data pulled from Nautobot, and
records a `ComplianceTestResult` per rule/device pair. This model is the
entire value proposition of the app: compliance logic is expressed as Python,
not as a rigid rule-builder UI, so it can express arbitrary conditions
(regex matching, structured parsing, cross-field comparisons) that a
form-based rule engine cannot.

The cost of that flexibility is that the engine must execute Python source
text that was typed into a Nautobot form by a user, not written by an app
developer and shipped in a release. Any mechanism that takes a string and
turns it into executing code is inherently risky: naively calling `exec()`
on `rule_code` would hand the caller full access to the Python process — the
Nautobot ORM, environment variables and secrets, the filesystem, and the
network — with none of the isolation a full sandbox (subprocess, container,
VM) would provide. We need a decision, made once and applied consistently,
about how much of that risk this app accepts and what it does to reduce it.

## Decision

We use a two-layer approach, implemented in `validation.py` and `engine.py`
respectively. Neither layer is sufficient on its own; together they are the
full extent of the app's protection.

### Layer 1: static rejection (`validation.py`)

Every `ComplianceRule.rule_code` is parsed with `ast.parse()` at save time,
before anything is persisted. The parse tree is walked and the save is
rejected (raising `django.core.exceptions.ValidationError`, naming what was
rejected and why) if it contains:

- Any `Import` or `ImportFrom` node — imports are banned outright.
- A call to any of: `eval`, `exec`, `compile`, `__import__`, `open`,
  `globals`, `locals`, `vars`, `getattr`, `setattr`, `delattr`, `input`,
  `breakpoint`, `memoryview`.
- Any `Attribute` node whose `attr` starts and ends with `__` (blocks
  dunder-attribute access such as `__class__`, `__globals__`,
  `__subclasses__`, `__bases__` — the standard route from an ordinary object
  to `os`/`subprocess` even without an `import` statement).
- Any `Name` referring to `os`, `sys`, `subprocess`, `shutil`, `socket`,
  `pathlib`, `importlib`, or `builtins`.

This is a purely syntactic, allowlist-free rejection pass: it does not try
to prove `rule_code` is safe, only to catch the mechanisms above before the
rule is ever stored or run.

### Layer 2: restricted-namespace execution (`engine.py`)

At run time, `rule_code` is compiled and `exec`'d against an explicitly
constructed namespace — never the real `__builtins__`. The namespace
provides exactly:

- A builtins allowlist: `len str int float bool isinstance any all sorted
  enumerate zip min max sum abs round list dict set tuple range print`.
- One pre-injected module, `re`, and no others.

The engine inspects the signature of the single top-level function defined
in `rule_code` and calls it with the subset of `configuration` / `commands`
it declares, then maps the outcome to a `ComplianceTestResult`: no exception
is a pass, `AssertionError` is a fail (with `output` set to `str(exc)`), and
any other exception is an error (`output` set to `f"{type(exc).__name__}:
{exc}"`).

Layer 2 is built to assume layer 1 already ran, but does not depend on it —
a `rule_code` value that reached the engine without static validation (a
fixture, a direct ORM write, a future code path that skips `full_clean()`)
is still executed inside the same restricted namespace, not against real
builtins.

## Known limitations

This is **not a sandbox** in the sense of a subprocess, container, or VM
boundary. It is two layers of defence-in-depth against *mistakes and
low-effort mischief* by users who already hold Nautobot RBAC permission to
create or edit `ComplianceRule` objects. It is explicitly **not** a security
boundary against a determined attacker who has that permission. In
particular, this approach does not protect against:

- **Denial of service.** Nothing bounds CPU time, memory, or recursion depth.
  A rule containing `while True: pass` or an exponential-blowup regex will
  hang or exhaust the worker process running the Job. There is no timeout or
  resource limit at either layer.
- **Restricted-namespace escapes.** `exec()` with a curated builtins dict is
  a well-known incomplete sandbox: creative use of allowed pure-Python
  constructs (generators, closures, comprehensions, format-string
  internals, or gadgets discovered after this ADR was written) has
  historically been used to reach `object.__subclasses__()`-style escapes
  even when dunder-attribute access is filtered at the AST level. The
  dunder-attribute check in layer 1 substantially raises the bar but is not
  a proof of containment.
- **Data exfiltration via return value or side channel.** A rule can `print`
  arbitrarily (it's in the builtins allowlist) and can construct strings from
  whatever `configuration`/`commands` data it was given; nothing stops it
  from encoding data into `output` or raising exceptions with attacker-chosen
  messages. This is a low-severity concern (the "channel" is the very
  `ComplianceTestResult.output` field the rule is meant to populate) but it
  is not blocked.
- **Second-order code generation.** `ast.parse` sees the source text as
  submitted. It cannot detect logic that builds and executes new code
  indirectly through means not covered by the reserved-name and call-name
  checks above (e.g. string concatenation that only becomes a banned call
  name once assembled at runtime in a way that changes the resolved
  `Call.func` — the static pass matches on syntax, not on runtime values).
- **Process-level isolation.** All rules for a run execute in the same
  Python process as the Nautobot Job itself (no forked subprocess, no
  separate OS user, no filesystem or network namespace). A successful escape
  from the restricted namespace has the same reach as the Job process,
  including the Nautobot ORM and any credentials available to it.

Because of the above, **rule authorship must remain restricted to trusted,
permissioned users**, per the recommendation below. This design is
appropriate for reducing accidental breakage and casual misuse from users
who are supposed to be writing compliance assertions, not for running rules
submitted by arbitrary or unauthenticated parties.

## Alternatives considered

### Subprocess with resource limits (rejected for v1)

Running each rule in a forked subprocess (or a small pool of worker
processes), with `resource.setrlimit` / `RLIMIT_CPU` / `RLIMIT_AS` and a
wall-clock timeout, would close the denial-of-service gap above and give
genuine process-level isolation (a rule can't reach Job-process memory or
the live Django/ORM state at all). This is the closest thing to a "true"
sandbox available without an external dependency.

It was rejected for v1 because it is materially more complex to implement
correctly (subprocess lifecycle management, serializing `configuration` /
`commands` across the process boundary, propagating `ComplianceTestResult`
data back, handling worker crashes and timeouts cleanly inside a Nautobot
Job) and Nautobot Jobs already run inside a Celery worker, which imposes its
own constraints on spawning and managing child processes. The two-layer
approach is a small fraction of the implementation cost and closes the most
likely failure mode (accidental misuse, not deliberate attack) that this
app's threat model actually cares about. Revisiting this is reasonable if
the threat model changes — see Recommendation below.

### RestrictedPython (rejected for v1)

[RestrictedPython](https://restrictedpython.readthedocs.io/) is a
purpose-built library for compiling a restricted AST and providing guarded
`__builtins__`, guarded attribute access, and guarded iteration. It is more
rigorous than a hand-rolled `ast.NodeVisitor` and is used in production by
tools with a similar "trusted-but-not-fully-trusted user writes a snippet"
model (e.g. Zope, Plone).

It was rejected for v1 because it is a new dependency (CLAUDE.md's
conventions call for not adding dependencies not named in the issue), it
has its own learning curve and failure modes (its guard functions must be
threaded through the exec namespace correctly or protection silently
degrades), and — critically — it solves the same problem this app's stated
threat model requires: containing *mistakes*, not a determined attacker. A
hand-rolled `ast.parse` pass plus a restricted builtins dict, both narrowly
scoped to this app's actual rule shape (one top-level function, no need for
classes, decorators, or complex control flow beyond what pytest-style
assertions need), is easier to audit in full than adopting and correctly
wiring up a general-purpose third-party guard library. If the threat model
changes, RestrictedPython is the natural first alternative to reconsider.

### Full sandbox (container / VM per rule run) (rejected for v1)

Spinning up an isolated container or VM per rule execution would give the
strongest isolation of any option considered, at the cost of infrastructure
this app does not otherwise need (an orchestration layer, image builds,
significant latency per rule, and operational surface far beyond what a
Nautobot Job normally requires). This is disproportionate to the stated
threat model of trusted-but-imperfect internal users and was rejected
without further prototyping.

## Recommendation

Because this design is defence-in-depth rather than a hard security
boundary, the operational safeguard that actually matters is **restricting
who can create or edit `ComplianceRule` objects**. Nautobot's RBAC
(object permissions on the `ComplianceRule` model) should be configured so
that `add_compliancerule` and `change_compliancerule` are granted only to
users who are trusted to run arbitrary Python inside the Job worker process
— the same level of trust an organization would extend to someone who can
edit a Nautobot Job's source directly. Read access (viewing rules and their
results) can be broader; write access to `rule_code` should not be.
