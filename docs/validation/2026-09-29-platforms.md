# Native platform delivery — 2026-09-29

Base `086e90c`. User confirmed Codex, Gemini CLI, Cursor and GitHub Copilot CLI,
then changed publication to eight pushes each (32 total). No paid runs authorized.

## Codex, parts 1–8

1. `74d6149`: event/root contract; three tests failed before implementation.
2. `d18f92c`: explicit outcomes; eight new cases failed first; 41 focused checks passed.
3. `a119ede`: shared response collection and native launcher; 50 native/Claude checks passed.
4. `ba36440`: generated wiring and self-contained bundle; 16 checks and plugin-creator manifest validation passed.
5. `d06382b`: project setup/removal; 19 checks passed. The original quoted-path probe varied project cwd, not the launcher path; final review exposed and corrected that coverage gap.
6. `dd9e581`: configuration doctor and subprocess receipt lifecycle; 28 checks passed.
7. `98295a9`: duplicate delivery, continuation and directory binding; three regressions observed failing, then 60 native/Claude checks passed.
8. `3d8f354`: documentation and rendered architecture. Architecture check: 77 nodes, 166 edges, all four tabs draw.

Bundle development exposed a wrong source-parent selection before publication;
it was corrected to copy only `core/` and launchers. The temporary build was
removed. The development-only manifest validator required PyYAML, installed in
the local virtual environment; the shipped runtime remains standard library.

Codex `--version` and `--help` executed locally (`0.158.0-alpha.2.1`). Payload
fixtures are explicitly documented-contract examples, not live host captures.
No installed-session compatibility or minimum-version guarantee is claimed.
Unknown prose outcomes remain incomplete rather than guessed success.

## Gemini CLI, parts 9–16

Native lifecycle, structured outcomes, response translation, extension
packaging, settings merging and diagnostics were delivered in six parts:
`378abd3`, `05763f2`, `9a2d70a`, `5612ffd`, `8f4d5d4`, `7ce0a42`.
The seventh part (`a675f57`) hardens background/directory/error handling and mixed hook
groups. Its final integration group passed **87 tests**, including Claude,
Codex, Gemini, setup, packaging, doctor and startup checks. The eighth part (`36d4477`) updates documentation and architecture.

Source review of Google's shell implementation established that native data can
carry explicit nonzero status and that ordinary display content can omit it.
Fixtures remain labeled schema/source examples. No real Gemini CLI session or
paid model call was executed. Prose-only success is deliberately incomplete.

## Cursor Agent, parts 17–24

Event/root mapping, structured output, response translation, native packaging,
project setup and doctor were published as `c4c1f96`, `8d53ba4`, `40990c5`,
`da913eb`, `54d297a`, `6f78cca`. Part 7 (`aa7010c`) fixes cancelled completion,
out-of-workspace cwd and an actual asynchronous startup/task overwrite race.
Four regression cases failed before correction; the final focused integration
group passed **212 tests**, including existing task handling. Part 8 (`a9afa01`) is the documentation/architecture publication.

No live Cursor application was run. Ordinary Stop has no report response field,
so documentation points to persisted status. CLI/cloud compatibility is not
inferred from the desktop contract.

## Copilot CLI, parts 25–32

Native camelCase lifecycle/tool mapping (`7a966b0`), explicit outcome boundaries
(`8d0ffea`), native responses (`c63d8b6`), direct-executable plugin packaging
(`2797ec5`), reversible project setup (`c336099`) and configuration doctor with
launcher receipts (`c9dc34f`) complete the first six parts. Part 7 (`518411d`)
handles cancellation and shared independent-review corrections. Part 8 is the
containing final documentation and rendered architecture publication.

The package/adapter group passed 27 tests; setup expansion passed 34; the doctor
and real launcher receipt group passed 42. These fixtures deliberately distinguish
numeric process statuses from successful tool transport, which alone remains
incomplete. No live Copilot CLI session was executed.

## Final integration and independent review

At the integration boundary, the full local Python 3.13 run passed **1,024 tests
with 28 skips in 271.37 seconds**. Subsequent final review changes and added
concurrency/path cases were checked in the native/task group: **210 passed in
58.38 seconds**. The correction/process group passed **75 with 2 POSIX-only
skips in 13.23 seconds**. Counts describe these individual runs; they are not a
claim that the final collection still has the earlier size.

Commands used (unique local temporary roots and cache directories omitted):

```sh
python -m pytest -q
python -m pytest tests/test_host_codex.py tests/test_host_gemini.py tests/test_host_cursor.py tests/test_host_copilot.py tests/test_host_packages.py tests/test_host_setup.py tests/test_host_doctor.py tests/test_tasks.py -q
python -m eval.validate
python plugin/bin/ep_doctor.py --host
python architecture/check.py --render
```

The existing Claude launcher doctor passed all checks; all four grader controls
were classified correctly. Architecture has **80 nodes and 170 edges across
seven planes**, with all four views rendered. The first final render caught an
oversized box subtitle; shortening it produced a fully successful repeat.

One independent whole-delivery reviewer returned four important findings:

1. A failed receipt save consumed the native tool identity. A regression failed
   with zero receipts on retry. Delivery identities now commit atomically with
   ledger observations, and concurrent duplicate delivery produces one receipt.
2. Windows argument quoting did not protect a launcher in `R&D`. The failing
   real invocation is now green using encoded PowerShell literals; additional
   actual launcher paths cover spaces, percent signs, quotes and Unicode.
3. Doctor stayed green after the launcher disappeared. The missing-launcher
   regression now fails configuration health without executing arbitrary hooks.
4. Native patch paths were silently absent in non-Git/already-dirty projects.
   Such events now open a conservative claim and retain an attribution warning;
   the task stays UNVERIFIED. Complete native patch attribution is deferred to
   real producer capture, and is not claimed as solved.

Cancelled Copilot completion was also seen failing before the fix, then passing.
The review excluded live-host/paid/Snag experiments, in-progress Copilot setup
and doctor, final push accounting, and deliberate POSIX process-group escape.
Those boundaries are explicitly accepted; setup/doctor were completed and tested,
and publication accounting is checked using Git.

## Final runtime CI matrix

[Run 36530709458](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/36530709458)
completed successfully on runtime commit `518411d` before the final documentation
push. Every job also passed all four grader controls and the Claude launcher
replay doctor.

| Runner | Full regression suite | Separate audit probes |
|---|---|---|
| Ubuntu, Python 3.11 | 1,024 passed, 31 skipped; 76.40 s | 102 passed, 2 skipped |
| Ubuntu, Python 3.13 | 1,024 passed, 31 skipped; 73.32 s | 102 passed, 2 skipped |
| Windows, Python 3.11 | 1,025 passed, 30 skipped; 255.54 s | 104 passed |
| Windows, Python 3.13 | 1,025 passed, 30 skipped; 258.72 s | 104 passed |

This matrix covers the final runtime and test changes. The following part changes
only documentation and the architecture visualization. Local documentation
validation resolved all 128 checked relative links with no missing targets;
`git diff --check` reported no whitespace errors.

## Linux process-probe investigation

Earlier CI runs `36527051944` and `36526987434` failed the keyboard-interrupt
five-second descendant-survival assertion. Run `36527129847` also exposed a
process disappearing between `/proc` existence and read. The latter was reproduced
with a deterministic disappearing-process probe: the prior helper raised
`ProcessLookupError`; the corrected helper returned false. Regression cases cover
both disappearance exceptions on POSIX. The five-second polling requirement is
unchanged; runtime process cleanup was not weakened or bypassed.

The separate descendant-survival assertion has **no established runtime cause**.
Source review found process-group termination in the cleanup path; the local
Windows process probes passed. Later successful matrix runs, including
`36529542722` on `c9dc34f`, do not establish that historical failure's cause.
This remains an explicit diagnostic limitation rather than an invented fix.

## Publication accounting

Each line below is a separately pushed commit from base `086e90c`; the containing
final documentation commit is part 32. Eight parts belong to each new platform.

| Part | Commit | Change |
|---|---|---|
| 1 | `74d6149` | feat(codex): define explicit native event and project boundaries |
| 2 | `d18f92c` | feat(codex): distinguish completed command outcomes from incomplete results |
| 3 | `a119ede` | feat(codex): connect native responses to the shared verification engine |
| 4 | `ba36440` | feat(codex): generate hook subscriptions and self-contained plugin bundles |
| 5 | `d06382b` | feat(codex): install project hooks without replacing existing configuration |
| 6 | `dd9e581` | feat(codex): diagnose native wiring and exercise command receipts through the launcher |
| 7 | `98295a9` | fix(codex): preserve task ownership and reject replayed or misbound results |
| 8 | `3d8f354` | docs(codex): publish native setup, validation boundaries and architecture |
| 9 | `378abd3` | feat(gemini): normalize native agent and tool lifecycle events |
| 10 | `05763f2` | feat(gemini): retain tool content and classify structured command outcomes |
| 11 | `9a2d70a` | feat(gemini): translate engine feedback into native context and retry decisions |
| 12 | `5612ffd` | feat(gemini): build native extensions with correctly scaled hook deadlines |
| 13 | `8f4d5d4` | feat(gemini): merge native hooks into project settings reversibly |
| 14 | `7ce0a42` | feat(gemini): expose native capability limits and verify launcher receipts |
| 15 | `a675f57` | fix(gemini): reject unfinished execution and preserve shared hook groups |
| 16 | `36d4477` | docs(gemini): publish extension setup, outcome limits and delivery evidence |
| 17 | `c4c1f96` | feat(cursor): normalize native events with explicit workspace selection |
| 18 | `8d53ba4` | feat(cursor): distinguish shell results from timeout and permission failures |
| 19 | `40990c5` | feat(cursor): translate native context, permission and completion responses |
| 20 | `da913eb` | feat(cursor): generate flat native hooks and portable Cursor plugin bundles |
| 21 | `54d297a` | feat(cursor): install versioned project hooks without replacing user entries |
| 22 | `6f78cca` | feat(cursor): diagnose native subscriptions and expose completion display limits |
| 23 | `aa7010c` | fix(cursor): preserve newer tasks during startup and skip cancelled completion |
| 24 | `a9afa01` | docs(cursor): publish native setup, workspace behavior and measured limits |
| 25 | `7a966b0` | feat(copilot): normalize native CLI events and tool arguments |
| 26 | `8d0ffea` | feat(copilot): keep transport success distinct from command evidence |
| 27 | `c63d8b6` | feat(copilot): translate CLI permissions, context and completion decisions |
| 28 | `2797ec5` | feat(copilot): generate direct-executable native plugin bundles |
| 29 | `c336099` | feat(copilot): install reversible project hook subscriptions |
| 30 | `c9dc34f` | feat(copilot): diagnose native wiring and verify launcher receipts |
| 31 | `518411d` | fix(hosts): persist receipt delivery atomically and harden native setup |
| 32 | Containing documentation commit | All five platforms, final guide/status/journey/validation and rendered architecture |

## Cross-platform acceptance boundary

Full Snag CI and live installed-host sessions remain unverified. Host trust is
not bypassed. No change in paid research outcomes is implied by adapter tests.

Gemini CLI, Cursor and Copilot applications were not found on PATH during discovery; this does not establish whether they are installed elsewhere. Native plugin-root resolution and host trust still require an installed-session acceptance check.
