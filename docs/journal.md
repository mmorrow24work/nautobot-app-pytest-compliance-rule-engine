# Build Journal

Per-issue record of the unattended (Lane B) build of
`nautobot-app-pytest-compliance-rule-engine`. One entry per Claude run, appended
automatically by `.github/workflows/claude.yml`.

## How this file is written

**Entries are appended by the workflow on `master`, not by Claude inside its PR.**
This is deliberate. In the `uk-wealth-tracker` build, having Claude append a
journal entry within each PR meant every open PR touched the same file, so
almost every one went `CONFLICTING` the moment any other PR merged — leaving
green, auto-merge-enabled PRs sitting unmerged indefinitely. Patching from the
workflow after the run sidesteps that entirely: Claude's branches never touch
`docs/journal.md`.

The trade-off is that entries carry **metrics, not prose**. The reasoning for
each change lives in the linked PR description. If an entry deserves narrative,
add it by hand under the entry's `### Notes` heading.

## Where the numbers come from

Claude Code writes a JSON transcript of every session to `execution_file` on the
runner. That path is on the **ephemeral** Actions runner and is destroyed when
the job ends — nothing GitHub retains can reconstruct the input/output token
split after the fact.

So the workflow does two things, both with `if: always()` so they survive a
failed or turn-capped run:

1. **Uploads `execution_file` as a build artifact** (90-day retention). This is
   the raw record and the belt-and-braces guarantee that no run data is lost.
2. **Appends a metrics entry to this file** and pushes it to `master`.

`execution_file` is written *before* the action raises its terminal error, so
metrics are captured even on an `error_max_turns` run — the failure cases are
exactly the ones worth measuring.

## What "Estimated Cost" means

This pipeline authenticates via a **Claude subscription** (OAuth), not
pay-per-token API billing. The cost figure is derived from the run's token
counts at standard list rates: it is what the run *would have* cost if metered.

**It is not a charge.** Subscription usage generates no incremental per-issue
cost; actual spend is the flat monthly fee regardless of how many issues run.
The figure is useful only as a consistent yardstick for comparing runs.

## Entry format

```
## <ISO date> — Issue #N: <title>

- **Result:** success | failure (<reason>)
- **PR:** #NN (or —)
- **Milestone:** MX
- **Model:** claude-sonnet-5 | claude-opus-5
- **Execution Duration:** NNN seconds
- **Turns:** NN
- **Input Tokens:** NN
- **Output Tokens:** NN
- **Estimated Cost:** $N.NNNN (notional — see above)
- **Run:** <actions run URL>

### Notes
(optional, hand-written)
```

## Build velocity

Recomputed from every entry below on each run.

<!-- VELOCITY_START -->
| Metric | Value |
|---|---|
| Issues with recorded metrics | 5 |
| Successful runs | 5 |
| Mean time per issue | 4m 58s |
| Mean turns per issue | 68 |
| Mean output tokens per issue | 20,828 |
| Mean estimated cost per issue | $0.3131 |
<!-- VELOCITY_END -->

---

## Entries

<!-- ENTRIES_START -->
<!-- New entries are appended below this marker, newest last. -->

## 2026-08-12 — Issue #1: M0: Scaffold nautobot-pytest-compliance-rule-engine app structure

- **Result:** success
- **PR:** —
- **Milestone:** M0: Repo scaffolding & CI foundation
- **Model:** claude-sonnet-5
- **Execution Duration:** 28 seconds
- **Turns:** 11
- **Input Tokens:** 36
- **Output Tokens:** 937
- **Estimated Cost:** $0.0142 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31622254474

## 2026-08-12 — Issue #1: M0: Scaffold nautobot-pytest-compliance-rule-engine app structure

- **Result:** success
- **PR:** —
- **Milestone:** M0: Repo scaffolding & CI foundation
- **Model:** claude-sonnet-5
- **Execution Duration:** 256 seconds
- **Turns:** 95
- **Input Tokens:** 308
- **Output Tokens:** 20747
- **Estimated Cost:** $0.3121 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31623361217

## 2026-08-12 — Issue #2: M0: GitHub Actions CI workflow with Postgres/Redis service containers

- **Result:** success
- **PR:** #32
- **Milestone:** M0: Repo scaffolding & CI foundation
- **Model:** claude-sonnet-5
- **Execution Duration:** 591 seconds
- **Turns:** 78
- **Input Tokens:** 238
- **Output Tokens:** 22160
- **Estimated Cost:** $0.3331 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31645573287

## 2026-08-12 — Issue #3: M0: Packaging, lint config, and pre-commit hooks

- **Result:** success
- **PR:** #33
- **Milestone:** M0: Repo scaffolding & CI foundation
- **Model:** claude-sonnet-5
- **Execution Duration:** 136 seconds
- **Turns:** 67
- **Input Tokens:** 212
- **Output Tokens:** 8721
- **Estimated Cost:** $0.1315 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31648151026

## 2026-08-12 — Issue #4: M1: ComplianceRule model

- **Result:** success
- **PR:** #34
- **Milestone:** M1: Data models
- **Model:** claude-sonnet-5
- **Execution Duration:** 482 seconds
- **Turns:** 89
- **Input Tokens:** 270
- **Output Tokens:** 51574
- **Estimated Cost:** $0.7744 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31648751406
