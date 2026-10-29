# Multi-stage v2 — pilot run; no real headroom

Superseded by [v3](../multistage-v3/README.md), whose cases are built so a
dependent is hard to find.

**Pilot, 2026-10-28** ([`pilot-collected.json`](pilot-collected.json), sealed
[`pilot-protocol.json`](pilot-protocol.json), [qualification](qualification.json),
[journey 92](../../journey/92-the-pilot-found-nothing-to-prevent.md)). Four
conversations, 24 stages, all completed and qualified, $3.39, Sonnet 5.5 medium,
superpowers 7.0.0 in both arms.

| | lost earlier groups | stale facts (mechanical) | cost | model time |
|---|---|---|---|---|
| superpowers, `access_policy` | 0 | 0 | $0.59 | 185 s |
| superpowers, `layered_config` | 0 | 2 | $0.96 | 332 s |
| + ElevenPowers, `access_policy` | 0 | 1 | $0.85 | 471 s |
| + ElevenPowers, `layered_config` | 0 | 2 | $1.00 | 457 s |

Every stale fact is an oracle defect: the agents documented their code
accurately, but chose behaviour no request stated and no group required.
`msg.lookup` assumes the reference also changed the command line, and
`lint.redundant-role` matches a placeholder's spelling. The frozen go rule is met
mechanically, not in substance. The superpowers arm made no mistake the
experiment counts, so per the design the stages are redesigned before any
further spending, and the oracle defects are fixed by a general rule. Pilot runs
are excluded from any analysis.

Two harness changes were made at qualification, before any paid stage. The Skill
tool is allowed in both arms; the held-out launcher's list left it out, so
superpowers' skills could not load. The user's own `~/.claude/CLAUDE.md` is now
excluded from every subscription run.

## The $0 phase

**The twelve projects are published at
<https://github.com/SatyamSingh-Git/elevenpowers-multistage-cases>** (commit
`d081cad`). Its `manifest.json` is the freeze of this repository at `d7bc394`,
and a fresh clone was checked file by file against the case hashes. The copy under
`eval/multistage_cases/` stays the one the harness reads.

The comparison designed in
[`2026-10-23-multistage-field-claims-design.md`](../../docs/superpowers/specs/2026-10-23-multistage-field-claims-design.md)
tests the two effects in the [field report](../../docs/field/2026-10-real-project.md):
whether later steps break work done in earlier ones, and whether docs are kept
current under a `CLAUDE.md` rule. It compares superpowers alone with superpowers
plus ElevenPowers, on projects that evolve through six requests in one
conversation. Everything in this section was built and checked without a model,
before the pilot.

## The twelve cases

Each case is a small standard-library Python project with its own tests, a
`docs/reference.md` table of documented facts, a `CHANGELOG.md`, a protected
file and the four `CLAUDE.md` rules. Each has six requests: at least four
cross-cutting (they change something other code depends on without naming
it) and at least one self-contained. Hidden pytest groups check behaviour,
cumulatively. Fresh agents wrote the cases from the
[authoring brief](../../eval/multistage_cases/AUTHORING.md) and were told
nothing about ElevenPowers.

| case | source lines | domain |
|---|---|---|
| `access_policy` | 789 | role and attribute access policies |
| `cronish` | 615 | schedule expressions |
| `eventlog` | 759 | append-only event log on disk (persisted format) |
| `invoice_calc` | 639 | invoices, tax and rounding |
| `layered_config` | 688 | layered configuration loader |
| `ledgerbook` | 697 | double-entry ledger with a persisted journal |
| `marklite` | 842 | markdown-subset renderer |
| `stockroom` | 668 | inventory with a JSON store (persisted format) |
| `tabulate_report` | 652 | CSV reports |
| `throttle` | 644 | rate limiting |
| `tinyroute` | 736 | URL router |
| `unitconv` | 652 | unit conversion |

## How each case was checked

- **Rehearsal (no model).** For every stage, the reference passes all its
  groups, documents every fact and keeps the rules. Each broken variant is
  caught by the check meant to catch it:
  - leaving a dependent behind fails exactly the earlier groups named;
  - keeping the previous stage's docs leaves exactly that stage's facts stale;
  - doing nothing fails the stage's new groups.

  All twelve cases rehearse usable from a fresh clone with `core.autocrlf=true`
  ([`rehearsal.json`](rehearsal.json)).
- **Two independent review rounds** ([`review.json`](review.json)). Round one
  found six blocking problems: correct alternatives that would have been graded
  as failing, or requirements no request stated. It also found invented fact
  keys and free-text values in ten of twelve cases. The brief then gained its
  fairness rules: a graded fact's key is an existing row or a name the request
  uses, its value is stated in the request, and groups require only what is
  stated. Every case was revised. Round two cleared every case once six
  remaining wording points in three requests were fixed.
- **Byte-exact storage.** `.gitattributes` keeps the case files byte-exact. A
  CRLF checkout made every stage diff fail to apply until it was added; that
  was watched flipping.

## Size and power

[`power.json`](power.json) simulates the pre-fixed analysis: an exact two-sided
signed-rank test over cases at alpha 0.025, Holm's first step for the two
co-primary outcomes. With 8 cases the test cannot reject unless 7 of them
differ. That is why twelve cases were written instead of the design's eight.
At ratio 0.5, about 0.8 power needs an arm-A rate of about 2 lost groups or
stale facts per conversation with 3 replicates, or about 4 with 2. The pilot's
measured rates choose the layout.

## Frozen

[`manifest.json`](manifest.json) records:
- the hash of every case file, the four modules and the brief, at the frozen
  commit;
- the fixed analysis;
- the pilot cases, chosen by seeded hash before any outcome: `access_policy`
  and `layered_config`.

Reproduce with `python results/multistage/freeze.py`. Pilot runs are excluded
from the analysis, and no case is dropped or replaced on its pilot result.

## What this does not show

The pilot is four conversations on two cases, excluded from analysis by design,
and supports no comparison between the arms. The cases are authored to contain
dependents and documented facts, which is what the claims are about. A
result will say whether the effect appears where it should, not how often such
stages occur in real work.
