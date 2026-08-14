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
| Issues with recorded metrics | 30 |
| Successful runs | 30 |
| Mean time per issue | 7m 06s |
| Mean turns per issue | 112 |
| Mean output tokens per issue | 31,859 |
| Mean estimated cost per issue | $0.5225 |
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

## 2026-08-12 — Issue #34: M1: Add ComplianceRule model

- **Result:** success
- **PR:** #34
- **Milestone:** —
- **Model:** claude-sonnet-5
- **Execution Duration:** 206 seconds
- **Turns:** 66
- **Input Tokens:** 208
- **Output Tokens:** 15119
- **Estimated Cost:** $0.2274 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31649458651

## 2026-08-12 — Issue #34: M1: Add ComplianceRule model

- **Result:** success
- **PR:** #34
- **Milestone:** —
- **Model:** claude-sonnet-5
- **Execution Duration:** 131 seconds
- **Turns:** 46
- **Input Tokens:** 144
- **Output Tokens:** 9327
- **Estimated Cost:** $0.1403 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31649828321

## 2026-08-13 — Issue #5: M1: ComplianceTestResult model

- **Result:** success
- **PR:** #35
- **Milestone:** M1: Data models
- **Model:** claude-sonnet-5
- **Execution Duration:** 513 seconds
- **Turns:** 146
- **Input Tokens:** 452
- **Output Tokens:** 37353
- **Estimated Cost:** $0.5617 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31664237811

## 2026-08-13 — Issue #6: M1: ComplianceRuleSet model

- **Result:** success
- **PR:** #36
- **Milestone:** M1: Data models
- **Model:** claude-sonnet-5
- **Execution Duration:** 496 seconds
- **Turns:** 152
- **Input Tokens:** 480
- **Output Tokens:** 33634
- **Estimated Cost:** $0.5060 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31665159026

## 2026-08-13 — Issue #7: M1: Model layer test coverage review

- **Result:** success
- **PR:** #37
- **Milestone:** M1: Data models
- **Model:** claude-sonnet-5
- **Execution Duration:** 127 seconds
- **Turns:** 41
- **Input Tokens:** 132
- **Output Tokens:** 8721
- **Estimated Cost:** $0.1312 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31665981001

## 2026-08-13 — Issue #10: M2: Sandboxing design doc / ADR

- **Result:** success
- **PR:** #38
- **Milestone:** M2: Sandboxed rule execution engine
- **Model:** claude-sonnet-5
- **Execution Duration:** 119 seconds
- **Turns:** 25
- **Input Tokens:** 80
- **Output Tokens:** 8018
- **Estimated Cost:** $0.1205 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31683741815

## 2026-08-13 — Issue #8: M2: Static validation (ast.parse) for rule_code safety

- **Result:** success
- **PR:** #39
- **Milestone:** M2: Sandboxed rule execution engine
- **Model:** claude-opus-5
- **Execution Duration:** 393 seconds
- **Turns:** 59
- **Input Tokens:** 168
- **Output Tokens:** 28393
- **Estimated Cost:** $0.7107 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31686977928

## 2026-08-13 — Issue #9: M2: Restricted-namespace execution engine

- **Result:** success
- **PR:** #40
- **Milestone:** M2: Sandboxed rule execution engine
- **Model:** claude-opus-5
- **Execution Duration:** 916 seconds
- **Turns:** 86
- **Input Tokens:** 263
- **Output Tokens:** 42127
- **Estimated Cost:** $1.0545 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31688154315

## 2026-08-13 — Issue #11: M3: RunComplianceRules Job — input form

- **Result:** success
- **PR:** #41
- **Milestone:** M3: Job execution & device data gathering
- **Model:** claude-sonnet-5
- **Execution Duration:** 484 seconds
- **Turns:** 139
- **Input Tokens:** 438
- **Output Tokens:** 35892
- **Estimated Cost:** $0.5397 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31724834334

## 2026-08-13 — Issue #12: M3: Optional Golden Config integration

- **Result:** success
- **PR:** #42
- **Milestone:** M3: Job execution & device data gathering
- **Model:** claude-sonnet-5
- **Execution Duration:** 206 seconds
- **Turns:** 72
- **Input Tokens:** 228
- **Output Tokens:** 15511
- **Estimated Cost:** $0.2333 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31726131411

## 2026-08-13 — Issue #13: M3: Live device data gathering (NAPALM/Netmiko)

- **Result:** success
- **PR:** #43
- **Milestone:** M3: Job execution & device data gathering
- **Model:** claude-sonnet-5
- **Execution Duration:** 444 seconds
- **Turns:** 117
- **Input Tokens:** 372
- **Output Tokens:** 34907
- **Estimated Cost:** $0.5247 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31726977390

## 2026-08-13 — Issue #20: M5: REST API — ComplianceRule and ComplianceRuleSet CRUD

- **Result:** success
- **PR:** #44
- **Milestone:** M5: REST API
- **Model:** claude-sonnet-5
- **Execution Duration:** 533 seconds
- **Turns:** 167
- **Input Tokens:** 520
- **Output Tokens:** 38738
- **Estimated Cost:** $0.5826 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31751308672

## 2026-08-13 — Issue #44: M5: REST API — ComplianceRule and ComplianceRuleSet CRUD

- **Result:** success
- **PR:** #44
- **Milestone:** —
- **Model:** claude-sonnet-5
- **Execution Duration:** 369 seconds
- **Turns:** 101
- **Input Tokens:** 302
- **Output Tokens:** 23565
- **Estimated Cost:** $0.3544 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31752468769

## 2026-08-13 — Issue #11: M3: RunComplianceRules Job — input form

- **Result:** success
- **PR:** #45
- **Milestone:** M3: Job execution & device data gathering
- **Model:** claude-sonnet-5
- **Execution Duration:** 374 seconds
- **Turns:** 146
- **Input Tokens:** 452
- **Output Tokens:** 28173
- **Estimated Cost:** $0.4240 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31753348611

## 2026-08-13 — Issue #14: M3: Wire execution engine into the Job

- **Result:** success
- **PR:** #46
- **Milestone:** M3: Job execution & device data gathering
- **Model:** claude-opus-5
- **Execution Duration:** 764 seconds
- **Turns:** 142
- **Input Tokens:** 433
- **Output Tokens:** 56886
- **Estimated Cost:** $1.4243 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31754222026

## 2026-08-14 — Issue #46: M3: Wire the execution engine into the RunComplianceRules Job (#14)

- **Result:** success
- **PR:** #46
- **Milestone:** —
- **Model:** claude-sonnet-5
- **Execution Duration:** 372 seconds
- **Turns:** 105
- **Input Tokens:** 330
- **Output Tokens:** 27567
- **Estimated Cost:** $0.4145 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31755499850

## 2026-08-14 — Issue #15: M3: End-to-end Job integration test suite

- **Result:** success
- **PR:** #47
- **Milestone:** M3: Job execution & device data gathering
- **Model:** claude-sonnet-5
- **Execution Duration:** 414 seconds
- **Turns:** 126
- **Input Tokens:** 398
- **Output Tokens:** 35879
- **Estimated Cost:** $0.5394 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31756296868

## 2026-08-14 — Issue #16: M4: List/detail/edit/delete views for ComplianceRule and ComplianceRuleSet

- **Result:** success
- **PR:** —
- **Milestone:** M4: Views & UI
- **Model:** claude-sonnet-5
- **Execution Duration:** 726 seconds
- **Turns:** 235
- **Input Tokens:** 11214
- **Output Tokens:** 62694
- **Estimated Cost:** $0.9741 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31773549388

## 2026-08-14 — Issue #17: M4: Filterable ComplianceTestResult results table

- **Result:** success
- **PR:** #49
- **Milestone:** M4: Views & UI
- **Model:** claude-sonnet-5
- **Execution Duration:** 546 seconds
- **Turns:** 154
- **Input Tokens:** 492
- **Output Tokens:** 47507
- **Estimated Cost:** $0.7141 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31774572792

## 2026-08-14 — Issue #49: M4: Add filterable ComplianceTestResult results table

- **Result:** success
- **PR:** #49
- **Milestone:** —
- **Model:** claude-sonnet-5
- **Execution Duration:** 603 seconds
- **Turns:** 176
- **Input Tokens:** 538
- **Output Tokens:** 50743
- **Estimated Cost:** $0.7628 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31775613531

## 2026-08-14 — Issue #49: M4: Add filterable ComplianceTestResult results table

- **Result:** success
- **PR:** #49
- **Milestone:** —
- **Model:** claude-sonnet-5
- **Execution Duration:** 535 seconds
- **Turns:** 124
- **Input Tokens:** 386
- **Output Tokens:** 47223
- **Estimated Cost:** $0.7095 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31776601034

## 2026-08-14 — Issue #18: M4: Device detail page tab injection

- **Result:** success
- **PR:** #50
- **Milestone:** M4: Views & UI
- **Model:** claude-sonnet-5
- **Execution Duration:** 618 seconds
- **Turns:** 206
- **Input Tokens:** 668
- **Output Tokens:** 43101
- **Estimated Cost:** $0.6485 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31781293033

## 2026-08-14 — Issue #50: M4: Add Compliance tab to Device detail page

- **Result:** success
- **PR:** #50
- **Milestone:** —
- **Model:** claude-sonnet-5
- **Execution Duration:** 615 seconds
- **Turns:** 174
- **Input Tokens:** 554
- **Output Tokens:** 53923
- **Estimated Cost:** $0.8105 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31782558681

## 2026-08-14 — Issue #50: M4: Add Compliance tab to Device detail page

- **Result:** success
- **PR:** #50
- **Milestone:** —
- **Model:** claude-sonnet-5
- **Execution Duration:** 144 seconds
- **Turns:** 45
- **Input Tokens:** 146
- **Output Tokens:** 9833
- **Estimated Cost:** $0.1479 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31783899339

## 2026-08-14 — Issue #19: M4: Dashboard summary widget

- **Result:** success
- **PR:** #51
- **Milestone:** M4: Views & UI
- **Model:** claude-sonnet-5
- **Execution Duration:** 643 seconds
- **Turns:** 167
- **Input Tokens:** 516
- **Output Tokens:** 56801
- **Estimated Cost:** $0.8536 (notional — see above)
- **Run:** https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/actions/runs/31784556340
