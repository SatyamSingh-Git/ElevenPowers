# Literal native invocation qualification — 2026-10-08

Base `3103041`; branch `codex/native-command-recognition`. The generalized design
and plan preceded implementation. No new dependency, project-specific branch,
model call or default-on advisory was added. See
[design](../design/native-command-recognition.md),
[plan](../superpowers/plans/2026-10-08-native-command-recognition.md),
[guide](../../the-guide/command-capture.md) and
[process observations](../../results/native-command-recognition/README.md).

Witnessed failing controls: 17 parser failures before literal wrapper binding;
20 integration failures before shared directory checks, history/reuse and report
identity; one null-directory failure before distinguishing invalid metadata from
absence; two missing producer-interface failures before the process exercise.
The initial producer callback incorrectly used a contained-process API without
stdin support; it was corrected to the existing bounded replay-launcher pattern.

The parser/declaration group passed 64 controls; the initial integrated group
passed 87. After metadata hardening, the affected host, milestone, history,
budget, automatic-command and portable-report group passed **388 tests**. Further
outcome/producer controls and final integration results are recorded against
their actual commands and exact tested revision at delivery.

One fresh whole-branch review of `3103041..6881640` found two Important issues:
positional Cargo/Go/Swift selectors lost their scope after raw provenance was
restored, and Windows drive-relative paths could qualify a different Bash
directory. Eight failing controls witnessed those problems before repair.
Two further failing portability controls covered single quotes and Windows
rooted paths without a drive. The repaired invocation group passed **81 tests**;
scope now uses qualified identity and ambiguous path forms are excluded.
Parent traversal and UNC paths are also outside automatic equivalence. Existing
adapter rejection of malformed metadata and independent undeclared-runner
heuristics remain unchanged. Fresh installed delivery and general shell parsing
were explicitly outside this review's claim.

Twenty-four actual process controls qualified under Python 3.13.2 on Windows 11:
Python unittest and JavaScript npm CI, each through cmd and Git Bash, each with
six outcomes. Wrong-directory success and real interruption remained incomplete;
masked failure received no declared binding. Replay wrote no native activation
state. These are not installed-session or coding-benefit results. The original
four-session comparison and its source regrades remain unchanged.

Final model-free controls reproduce all eight published independent stage
grades. The host doctor and all four grader categories pass; new modules import
with `python -S` and no site packages. All five architecture views rendered at
**130 nodes / 300 edges / seven planes**, including contributor interactions and
narrow layout. CI imports the new runtime and producer modules without site
packages. Final local and hosted full-suite outcomes are delivery gates rather
than predicted counts in this record.

All **387 local documentation links** in the changed Markdown files resolve.

```sh
python -m pytest tests/test_command_invocations.py tests/test_invocation_capture.py tests/test_invocation_producers.py -q
python -m eval.command_invocations NEW_DISPOSABLE_DIRECTORY
python plugin/bin/ep_doctor.py --host
python -m eval.validate
python results/behavior-preservation/reproduce.py
python architecture/check.py --render
python -m pytest -q
```

Generic pytest fixtures must remain outside project Git boundaries. Use the
default system temporary root; do not put a non-Git fixture under this checkout.
Hosted exact-revision CI and main refs are final integration evidence. Broader
shell support, fresh installed capture and advice consumption remain open.
