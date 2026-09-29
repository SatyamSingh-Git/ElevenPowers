# Native platform delivery — 2026-09-29

Base `086e90c`. User confirmed Codex, Gemini CLI, Cursor and GitHub Copilot CLI,
then changed publication to eight pushes each (32 total). No paid runs authorized.

## Codex, parts 1–8

1. `74d6149`: event/root contract; three tests failed before implementation.
2. `d18f92c`: explicit outcomes; eight new cases failed first; 41 focused checks passed.
3. `a119ede`: shared response collection and native launcher; 50 native/Claude checks passed.
4. `ba36440`: generated wiring and self-contained bundle; 16 checks and plugin-creator manifest validation passed.
5. `d06382b`: project setup/removal; 19 checks including actual quoted-path execution passed.
6. `dd9e581`: configuration doctor and subprocess receipt lifecycle; 28 checks passed.
7. `98295a9`: duplicate delivery, continuation and directory binding; three regressions observed failing, then 60 native/Claude checks passed.
8. Documentation and rendered architecture, in the containing publication part. Architecture check: 77 nodes, 166 edges, all four tabs draw.

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
The seventh part hardens background/directory/error handling and mixed hook
groups. Its final integration group passed **87 tests**, including Claude,
Codex, Gemini, setup, packaging, doctor and startup checks. The eighth part is
this documentation and architecture update.

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
group passed **212 tests**, including existing task handling. Part 8 is the
containing documentation/architecture publication.

No live Cursor application was run. Ordinary Stop has no report response field,
so documentation points to persisted status. CLI/cloud compatibility is not
inferred from the desktop contract.

Earlier CI runs intermittently failed POSIX process-tree probes, including a
process disappearing while `/proc` was read. Later runs passed; those passes
do not by themselves explain the earlier failures. Final integration work must
investigate and record the failure rather than silently discarding it.

## Remaining platforms

GitHub Copilot CLI awaits its eight-part delivery.
Their live applications were not found on PATH during read-only discovery; this
does not establish whether the applications are installed elsewhere.

## Cross-platform acceptance boundary

Full Snag CI and live installed-host sessions remain unverified. Host trust is
not bypassed. No change in paid research outcomes is implied by adapter tests.
