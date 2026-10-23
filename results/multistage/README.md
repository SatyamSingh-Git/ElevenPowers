# Multi-stage v2 — frozen, no model run yet

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
conversation. **Everything here was built and checked without a model.** The
one-cent qualification, the pilot and the full run each wait for the user's go.

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

Nothing about either arm: no model has run. The cases are authored to contain
dependents and documented facts, which is what the claims are about. A
result will say whether the effect appears where it should, not how often such
stages occur in real work.
