# Fixed-patch review findings — 2026-10-02

All eight approved subscription reviews completed using observed
`claude-sonnet-5`, medium effort, through Claude Code 2.1.287. Each had a
480-second cap, one launch and no API fallback. Four selected upstream patches
received ordinary and ElevenPowers-assisted review from identical source and
existing-test inputs; an untouched checkpoint supplies the third comparison.
Only new test files were eligible. All eight preserved protected inputs and
added one file each.

## Measured outcome

| Case | Untouched detections | Ordinary review | Assisted review | Incremental assisted gain |
|---|---:|---:|---:|---:|
| ItsDangerous `6c58e969` | 6/8 | 6/8 | 6/8 | 0 |
| Click `ad39d749` | 2/8 + 1 setup | 2/8 + 1 setup | 2/8 + 1 setup | 0 |
| Jinja2 `065334d1` | 2/7 | 7/7 | 7/7 | 0 |
| attrs `97f8d175` | 2/2 | 2/2 | 2/2 | 0 |

These are frozen source-fault samples on already-correct real upstream patches,
not naturally occurring defects found in those production patches. Jinja2's
five previously missed faults had prior blinded Sonnet/Opus judgments of
MEANINGFUL. Both reviewers' new behavior tests detect all five while preserving
the full upstream suite and accepting the equivalent formatting control. This
demonstrates stronger tests from review; it does **not** demonstrate an additional
ElevenPowers quality benefit. All four completed matched pairs tie.

Click's two prior dual-rater meaningful survivors involve descriptor capture,
unsupported on Windows. Added descriptor tests skip here. Those labels cannot
establish an active Windows quality-gap endpoint. ItsDangerous survivors have
disputed/trivial prior labels; attrs starts with both sampled faults already
detected. Other detections are exploratory, with qualifications retained per
fault. Prior model labels are judgments, not infallible human ground truth.

All twelve untouched/review full suites pass and all twelve cosmetic controls
remain accepted. Counts are descriptive rather than a quality score:

| Case | Untouched passed/skipped | Ordinary passed/skipped | Assisted passed/skipped |
|---|---:|---:|---:|
| ItsDangerous | 399/0 | 403/0 | 404/0 |
| Click | 1459/86 | 1461/90 | 1464/87 |
| Jinja2 | 909/0 | 918/0 | 920/0 |
| attrs | 1388/7 | 1394/7 | 1394/9 |

## Time and analysis quality

| Case | Ordinary native review seconds | Assisted native review seconds |
|---|---:|---:|
| ItsDangerous | 58.984 | 84.900 |
| Click | 73.446 | 204.933 |
| Jinja2 | 93.370 | 127.089 |
| attrs | 61.859 | 115.438 |

Totals are 287.658 and 532.359 seconds respectively. These include native review
tools but exclude separate engine auditing and final grading. Assisted time was
greater in each selected pair; no speedup or population timing effect is established.
Subscription allowance was consumed, with no API fallback or charged API cost record.

The shipping Cosmic Ray 8.7.0 adapter used 180 seconds, 32 attempts and a
30-second command cap. Initial free whole-suite analysis is retained: Jinja2
and attrs had baseline timeouts; ItsDangerous supplied no completed survivor
lead; Click supplied one. Before calls, a second analysis froze relevant existing
public test modules as the treatment. Final grades still use full suites.
Focused attempt counts were 21, 24, 32 and 9 respectively, with deferred/incomplete
coverage. Function-level leads carried uncertainty, never mutant identities or
replacements.

Jinja2's producer-order sample did not reach changed `do_attr`; its 31 survivors
concerned earlier functions insufficiently tested by the focused security module.
attrs' survivor lead concerned `attrib`, outside the changed ClassVar helper.
This demonstrates a relevance limitation in whole-file bounded sampling. A
focused command's survivor may also be covered elsewhere by the ordinary suite.
The generalized changed-function/hunk selection delivery now addresses this
sampling limitation. Its new evidence must be read separately from this pilot;
the original whole-file observations remain unchanged.

## Reproduction, inspection and corrections

The [archive](2026-10-02-checkpoint-review/README.md) preserves portable source/fault
fixtures, all eight submitted tests and grades, native model/budget metadata,
whole/focused observations, original producer identities, environment limits
and upstream BSD-3-Clause/MIT notices. It omits private native streams, prompts,
tool payloads and captured outputs. Checksums validate internal consistency;
all eight recorded conditions qualify. Hashes are unsigned.

The producer was frozen at `87c882d` before calls. Independent review reproduced
five concrete defects: collection traceback text credited as detection, long
pytest summary counts lost, original `.claude` inputs omitted from sealing,
insufficient saved budget/model/grade validation, and absent formatting controls
qualifying through a vacuous predicate. Each failing regression was observed
before correction. The final focused suite passed **23 tests in 11.70s**; broader
parser compatibility passed **200 tests in 129.43s**. The full hosted Linux/Windows
Python 3.11/3.13 matrix passed at `de717825` in
[run 37036487827](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/37036487827).
The subsequent explicit-control correction has focused local verification;
final publication starts a fresh hosted run.

Final archive inspection passed, with all eight recorded conditions qualified
and the original/current harness difference explicit. Architecture validation
rendered all four tabs with **106 nodes and 243 edges**. Full local regression
was not rerun for this delivery; the preceding hosted full matrix and focused
local regressions are the actual verification evidence.

A separate full regrade under the corrected evaluator finished on 2026-10-03
after resumption: **all twelve saved grade sets completed in 1,461.765 seconds**.
Nine match historical states/counts exactly. Click F03 changes in all three
arms from credited detection to `setup`: the runs have actual test failures
together with 1,049 setup errors. The corrected table above retains that
incomplete state. Original case/review grades still contain the historical
3/8; the [separate reproduction](2026-10-02-checkpoint-review/reproduction-2026-10-03.json)
contains all current grades, grader hashes and explicit differences. All twelve
baselines and equivalent controls still pass. `grades_match: false` is expected
against those historical grades; `current_harness: false` identifies the
original producer difference. Jinja2's five-fault improvement for both arms,
and the absence of incremental assisted benefit, remain unchanged.

Independent inspection of all eight visible native traces found exact models,
matching seals and recaptured additions, with no observed forbidden retrieval
or delegation. Tests assert behavior rather than source spelling. Click has
platform-skipped FD checks; attrs' assisted Python 3.14-gated test has a name
broader than its actual assertion and skips here. Original submissions remain
unchanged and qualified in the archive.

CLI safe mode disabled ordinary customizations equally; three built-in plugin
metadata entries remained. No external MCP servers were present. Native Bash
and the interpreter's inherited system packages do not provide an OS exposure
boundary or hermetic environment. This explicit analysis consumer does not
establish automatic installed feedback, production repair, execution performance
or broad product efficacy. The resumed session completed free reproduction;
it launched no additional model experiments. See [journey 57](../../journey/57-a-review-needs-a-relevant-lead.md)
and [provenance](../research/checkpoint-review.md).
