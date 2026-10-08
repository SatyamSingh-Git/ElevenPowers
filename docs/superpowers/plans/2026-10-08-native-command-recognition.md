# Native command recognition implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this authorized change inline, task by task.

**Goal:** Bind conservative native directory wrappers to exact project-owned
commands, preserving provenance and later unsuccessful attempts.

**Architecture:** A standard-library invocation qualifier supplies the existing
parser and shared hook. Existing receipt fields carry observed and declared
identities; history, reporting and verification reuse consume the same identity.

**Tech stack:** Python standard library, pytest and actual local shell producers.

**Spec:** [design](../../design/native-command-recognition.md).

## Global constraints

- Generalized runtime; named projects are controls only.
- No model calls, new runtime dependencies or default activation changes.
- Keep old experiment archives and their producer identities unchanged.
- Run fixtures outside all project Git boundaries; never use a checkout-local
  pytest basetemp for non-Git controls.
- Push each verified meaningful increment; main integration uses standing
  authorization after exact-revision hosted CI.

## Review focus

Shell quoting and literal path parsing; working-directory attribution across
host ingress paths; incomplete attempts overriding older passing observations;
history/freshness compatibility with legacy and targeted receipts; accidental
equivalence of extra commands, arguments, pipelines or interpolation.

### Task 1: Literal wrapper and receipt qualification

Files: `core/commands.py`, `core/parsers.py`, invocation tests.

- [x] Write forward/adversarial directory, quoting, outcome and exact-match
  controls; observe missing wrapper qualification before implementing it.
- [x] Add bounded literal analysis; retain exact leaf identity and raw invocation.
  Reject unsupported automatic equivalences and preserve incomplete outcomes.
- [x] Run parser compatibility controls; push verified recognition.

### Task 2: Shared hook and evidence consumers

Files: `core/hook.py`, `core/evidence.py`, `core/verify.py`, milestone history/report.

- [x] Observe regressions for wrapper history, failed/interrupted supersession,
  fresh-result reuse, configuration movement and tool-directory mismatches.
- [x] Use qualified declared identity consistently; retain original provenance.
  Qualify all host ingress paths without trusting foreign-directory results.
- [x] Run affected host/milestone/verification tests and push the integration.

### Task 3: Producer controls and delivery

Files: model-free evaluation/results, guides, validation, journey, plan/status,
architecture and CI.

- [x] Run real shell commands on unrelated disposable projects with success,
  failure, wrong-directory and interruption controls; retain measured results.
- [x] Perform one fresh review and repair important findings with witnessed
  failing/passing controls. Update affected docs and architecture; render all tabs.
- [ ] Verify regressions and exact-head hosted CI, push final documentation,
  fast-forward main and verify the published architecture.
