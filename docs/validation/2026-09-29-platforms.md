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

## Remaining platforms

Gemini CLI, Cursor Agent and GitHub Copilot CLI await their eight-part deliveries.
Their live applications were not found on PATH during read-only discovery; this
does not establish whether the applications are installed elsewhere.

## Cross-platform acceptance boundary

Full Snag CI and live installed-host sessions remain unverified. Host trust is
not bypassed. No change in paid research outcomes is implied by adapter tests.
