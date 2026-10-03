# Changed-region strength and completed reproduction — 2026-10-03

The generalized runtime now records Git hunks, partitions broad/new-file changes
by function, requires complete mutation-span containment and rotates bounded
samples across files/functions. Mixed-language shares follow selected file
counts. Missing or removed behavior stays explicit; current source can still be
analyzed alongside deletion limitations. No repository name, project path or
project command is hardcoded in the runtime. All five hosts share this runner.

New schema-2 records contain bounded line spans, edit relationship, function
context, selection and recorded-command-only qualification. Old schema-1 samples
remain readable and unattributed. Human reports are read-only and show full
spans. There is no new completion blocker or raw mutation target in automatic
agent feedback. Optional pinned engines still require explicit installation.

## Free real-project relevance check

Four pinned upstream patches from the fixed-patch review archive were prepared
in fresh disposable repositories. A generation-only comparison used the same
Cosmic Ray 8.7.0 producer, current source and eight-candidate cap: historical
whole-file selection versus the new hunk/function selection. No model ran.

| Patch | Whole-file generation | Changed-region generation |
|---|---|---|
| ItsDangerous `6c58e969` | 8 candidates; seven in earlier `unsign`, one in `loads` | All 5 applicable candidates in edited `loads` |
| Click `ad39d749` | 8 candidates in module and several earlier functions | 8 candidates in changed `__init__`, `fileno`, `invoke`, `start`, `stop` contexts |
| Jinja2 `065334d1` | 8 candidates; none in edited `do_attr` | All 4 applicable candidates in edited `do_attr` |
| attrs `97f8d175` | All 8 candidates in earlier `attrib` | All 8 candidates in edited `_is_class_var` |

The counts describe this capped producer sample, not semantic coverage or a
coding-quality score. Changes within a function can include unchanged lines in
that function; the relation field distinguishes those from actual changed lines.
Complete spans must fit the selected target. Same-line functions remain ambiguous.

Separate targeted **test executions** used the previously selected focused
modules, 90 seconds total, eight attempts and 15 seconds per command. These are
different measurements from generation:

| Patch / focused command module | Baseline | Observed attempts | Qualification |
|---|---|---|---|
| ItsDangerous / `tests/test_itsdangerous/test_timed.py` | Passed | 5 detected | All applicable producer candidates completed |
| Click / `tests/test_testing.py` | Timed out | 0 | Incomplete; no detection/survival claim |
| Jinja2 / `tests/test_security.py` | Passed | 1 detected, 3 undetected | Only this focused command was measured |
| attrs / `tests/test_annotations.py` | Passed | 5 detected, 3 undetected | Additional candidates unexamined at the attempt cap |

Every baseline/attempt used fresh private inputs. Protected source, existing
tests and configuration inputs were unchanged after each case. The runtime code
identity was frozen before the audit and checked after each case. A preceding
development audit had a passing Click baseline; the final frozen audit above
retains its actual timeout instead of substituting that earlier result.

[The metadata artifact](2026-10-03-strength-regions.json) retains both generation
samples, actual targeted execution states, bounds, source locations and runtime
hashes. It contains no mutant replacements or captured output. The source cases
and BSD-3-Clause/MIT licenses remain in the
[fixed-patch archive](2026-10-02-checkpoint-review/README.md).

Host: Windows, Python 3.13.2, Cosmic Ray 8.7.0. The research interpreter inherited
system site packages; it was not hermetic. The filesystem copy/read guard is
diagnostic, not an OS sandbox. Hashes provide unsigned consistency, not native
run authentication. Undetected mutations may be equivalent, or detectable by
another test command. These observations establish improved **analysis
relevance**, not an incremental coding-quality, repair or speed advantage.

To repeat a case with a local Git cache, load its archived `case-*.json`, supply
the cache as `case['repository']`, and call
`eval.review_checkpoint.prepare(case, NEW_DISPOSABLE_DIRECTORY)`. The preparation
retains the upstream base/patch and creates a local base recorded in
`.ep-review-checkpoint.json`. Configure the trusted interpreter and focused test
module, then use:

```bash
python plugin/bin/ep_strength.py --root NEW_DISPOSABLE_DIRECTORY --base PREPARED_BASE --command "TEST_PYTHON ep_review_pytest.py FOCUSED_MODULE -q -p no:cacheprovider" --seconds 90 --max-mutants 8 --json
```

The default per-command cap is 15 seconds. Use the same pinned interpreter and
dependencies as the archive; machine scheduling can change timed-out outcomes.
Generation controls can call `core.strength.engines.cosmic` with `regions=None`
for the legacy sample and the `select(...).regions` mapping for targeted sampling.
Both calls must use fresh `Budget` objects with the same eight-candidate limit.
This is explicit local trusted-code execution, with no model or dependency install.

## Completed corrected-grader reproduction

All twelve untouched/ordinary/assisted grade sets finished in 1,461.765 seconds.
Nine match the historical states/counts exactly. In all three Click arms, F03
produces actual test failures together with 1,049 setup errors. The corrected
grader retains `setup`, rather than complete detection: **2/8 + 1 setup** replaces
the historical 3/8 for current interpretation. Frozen originals are unchanged.
The [separate corrected artifact](2026-10-02-checkpoint-review/reproduction-2026-10-03.json)
retains all twelve current grades, grader hashes and explicit corrections.

All twelve unmutated suites pass and equivalent formatting controls remain
accepted. Jinja2's five formerly missed faults are still detected by both
ordinary and assisted review. All four pairs still tie. No incremental product
quality benefit or speedup was established, and no new model calls were made.

## Review and verification

Real failing controls preceded fixes for original-path guard forwarding,
oversized/false location metadata, file imbalance, declared Python encodings,
broad-hunk function attribution, nested ancestor mutations, language starvation,
entire-file deletion, deletion suppressing available source and Markdown ranges.
Real Cosmic Ray and Stryker 9.5.1 JavaScript/TypeScript/TSX producer controls pass.
An independent reviewer reproduced four important boundary/coverage findings and
the multiline report issue; all were corrected. Its final nine focused controls
passed and it found no remaining critical or important issue.

The stable-code full regression result, rendered architecture checks and hosted
matrix are recorded at the final publication boundary below. Installed-host
acceptance and measured coding benefit remain separate open exits.
