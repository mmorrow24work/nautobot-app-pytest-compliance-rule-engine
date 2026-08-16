# Live device validation and self-hosted runners

M8's stretch goal ([#29](https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/issues/29)) is a
[containerlab](https://containerlab.dev/)-based integration harness that runs
`RunComplianceRules` against a real, simulated network device rather than mocked
configuration/command strings. This document explains why that harness can't run in
this repo's existing GitHub Actions CI, and the two ways forward if you want it
automated rather than manual.

## Why it can't run on GitHub-hosted runners

Every test in this repo up to and including M7 runs against Postgres and Redis
**service containers** started by the `test` workflow (`.github/workflows/test.yml`) --
that pattern works because GitHub-hosted runners can reach containers on their own
Docker network, and Postgres/Redis are the only external dependencies those tests have.

containerlab is different: it builds a small virtual network of container-based device
nodes (e.g. an Arista cEOS or Cisco XRd image) connected to each other, and
`RunComplianceRules` needs a real network path to log into one of those nodes and pull
live command output over NAPALM. GitHub-hosted runners are ephemeral VMs with no route
to that network -- there's nothing to `docker run` your way into reaching, unlike a
Postgres container, because a hosted runner has no persistent network namespace
containerlab can attach device nodes to, and no permission to run the privileged
container networking containerlab depends on. This isn't a configuration gap that a
different YAML setting fixes; it's a category of infrastructure GitHub-hosted runners
don't provide at all.

## Two paths forward

**(a) Register a self-hosted runner.** Add a GitHub Actions self-hosted runner on your
WSL2 environment (the same one used for the manual install step,
[#28](https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/issues/28)), with containerlab and Docker installed. A workflow job with
`runs-on: [self-hosted, containerlab]` (or similar label) can then reach real
containerlab nodes the same way the `test` job reaches its Postgres/Redis containers.
The tradeoff: CI now depends on a machine you maintain being online and reachable,
rather than solely on GitHub's infrastructure -- worth doing once this app has real
users depending on the live-validation signal, not before.

**(b) Keep it manual.** Run the containerlab harness by hand, on your WSL2 environment,
as a pre-release verification step -- after `nautobot-server test` passes in CI but
before tagging a release. This is the lower-commitment option and the one this repo
currently follows: nothing beyond Postgres/Redis-backed tests runs in CI, and live
device validation is a deliberate manual gate rather than an automated one.

## On "the main build plan's feasibility table"

The issue asks this document to link back to "the main build plan's GitHub-only
feasibility table." No such document exists in this repository -- there is no separate
build-plan file with a feasibility table to link to. The closest thing that does exist
is [`build/create-nautobot-issues.sh`](../build/create-nautobot-issues.sh), the script
that defines this repo's milestones and issues (including this one and [#29](https://github.com/mmorrow24work/nautobot-app-pytest-compliance-rule-engine/issues/29)) and the
`lane:unattended` / `lane:interactive` / `lane:manual` labels that encode, issue by
issue, what can run unattended in CI versus what needs a human or self-hosted
infrastructure. If a standalone feasibility-table document exists outside this repo,
it isn't something I have access to, and I didn't want to fabricate a link to a file
that isn't here.
