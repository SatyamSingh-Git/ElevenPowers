# Response — 19 September 2026

Written after acting on the audit, not instead of acting on it. Commits
`c754d6e`, `85aeb06`, `1a7d6e3`.

## Verification first

The audit shipped a runnable probe script. It was run here against `4e9b797`
before any code was read or changed, and **all fourteen probes reproduced
byte-for-byte**, matching the JSONL in [`evidence.md`](evidence.md) exactly.
Nothing below rests on agreeing with the report's reasoning.

The statistical objections were checked the same way: by running the arithmetic
and reading the papers' HTML, not by weighing the argument.

## Implementation findings

| | Finding | Status |
|---|---|---|
| F1 | Confirmation invents passes | **Fixed.** Outcomes read from `pytest -rA`; only an id named `PASSED` is credited. Fail-fast dropped for the confirmation run, `--maxfail N`'s value token handled |
| F2 | A question creates a proven checkpoint | **Fixed.** The snapshot asks `ledger.status()`, which is computed from evidence, not the `settle` value that grants permission to end a turn |
| F3 | Discrimination caches omit mutable inputs | **Fixed.** Keyed on base, command and the *content* of the carried tests. The related defect — a failed invocation spending the attempt — is fixed by writing the `CONFIRMED` note after the result is inspected |
| F4 | Unrelated checks joined into a reproduction | **Fixed.** The suite fallback requires the *tests* check to be the discriminating one |
| F5 | Reading a TAP file counts as a run | **Fixed.** The bare-header exception is withdrawn; a named harness or a command claiming tests is required, and TAP from neither writes a blindspot |
| F6 | Reading a file suppresses its edit brief | **Fixed.** Delivery tracked separately from observation (`ledger.briefed`). This also qualifies a published number — see below |
| F7 | Output capture incomplete; absence read as evidence | **Fixed, both halves.** Output is captured before the evidence decision, when a task is open; vacuity now requires an observed base-tree pass (`passed_before`) |
| F8 | The offered restore does not restore | **Fixed.** A worktree is offered first; files added since are counted and named; the in-place command is still offered when it is genuinely faithful |
| F9 | `off` dispatches verification work | **Fixed.** Profiles carry `verifies` separately from `speaks` |
| F10 | An unchanged file treated as wholly changed | **Fixed.** Presence in the base commit decides, via `ls-tree`; a git failure is not read as "new" |
| F11 | Redaction misses `Evidence.detail` | **Fixed.** Scrubbed at construction, so no unredacted copy exists in memory or on disk |
| F12 | `ALL POOLED` loses earlier attempts | **Fixed.** Attempts concatenate within a task |

Twenty tests added across two files. **Nineteen probes were watched red with
their fix removed and green with it restored.** Two of the new tests were
vacuous when first written and flipping found both; the forward control also
caught a defect inside one of the fixes before it shipped (`git cat-file -e`
answers 128 for both "absent" and "error", which are the two states that check
exists to separate).

Two of the audit's own probes cannot observe their fix through their own
mocking — `ordinary_producer_output_dropped` patches `Ledger.load`/`save` and so
never creates the state file the capture is now gated on, and
`restore_leaves_new_test` executes the old command literally rather than asking
what is offered. Both are covered by tests here instead.

## Reasoning and experimental design

**R1 — accepted, with the number kept as a reference point.** The four-point
threshold was being used as a universal cutoff that could cancel a phase. It is
one study's result about its own selectors on its own benchmark, and a
selector's value is rescued mass minus damaged mass. `HARM_LINE` remains as a
prior and a reason to look upstream first; it is no longer a decision rule.
PLAN §10.

**R2 — accepted.** The B6 design is qualified in place rather than resumed: one
replicate per arm can estimate an average treatment effect, replication competes
with task coverage, and the "31 discordants" figure came from power assumptions
for one alternative rather than a universal requirement.

**R3 — accepted; the arithmetic was wrong.** `~13%` was the rule of three
applied to one event. Corrected to **19.81%** one-sided, **22.84%** two-sided,
re-derived here. The pooling assumption is not defended either, and that is said
rather than fixed.

**R4 — accepted, and it found a second error.** The figure is **6.4**, not 6.2;
the source was graded `(snippet)` by the very file that warns against snippets.
And an absolute inflation is not a minimum detectable effect for a paired
design.

**R5, R6 — accepted as stated, not yet acted on.** These are research
directions, not defects. Nothing in them is disputed.

## What was **not** done, and why

The audit's largest recommendation is an architecture: separate executions,
observations, candidates and decisions; snapshot a candidate when qualifying
evidence arrives rather than at Stop; then build one complete path — early
issue-grounded reproduction, preserved incumbent, one alternative, conservative
selection — and compare it against a compute-matched baseline.

**None of that is built here, and the reason is money rather than disagreement.**
It is a paid experiment with a real budget, and this repository's own rule is
that paid runs are never started without asking. Stage 1 of the audit's own
sequence — restore evidence integrity — is what these three commits are, and it
is the stated prerequisite for the rest.

Two things are worth saying plainly to whoever picks this up:

- The audit is right that more diagnostics are not the bottleneck. This project
  has never demonstrated that it makes code better, and §10 records the
  measurements that failed to show it.
- The F6 finding is a warning about how the rest was measured. A detector
  measured by calling it is not a feature measured by using it, and at least one
  published figure here was the former presented as the latter.
