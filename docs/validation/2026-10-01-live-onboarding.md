# Generalized onboarding and live diagnostics — 2026-10-01

Runtime correction commit: `13c7ab9`. Additional generalized controls: `5858e79`.
Design: [live onboarding](../design/live-onboarding.md). Prior published baseline:
`4f194e7`. No paid evaluation or model prompt was run for this delivery.

## Local implementation checks

| Check | Actual result |
|---|---|
| Initial onboarding/setup/doctor controls | 28 passed |
| Native edit and host/package boundary | 115 passed |
| Final review corrections and startup controls | 43 passed |
| Unrelated manifest and parallel/project-isolation controls | 6 passed |
| Initial broad run, while corrections were landing | 1,055 passed / 28 skipped, 317.24 seconds |
| Settled final code and controls, Python 3.13.2 on Windows | **1,062 passed / 28 skipped**, 314.53 seconds |
| Grader controls | All four expected categories matched |
| Claude launcher doctor | All reported configuration, parser, launcher and stop checks passed |
| Architecture | **84 nodes / 180 edges / 7 planes**; all four views rendered |

The final suite used `--basetemp=.venv/final-onboarding-2026-10-01` and
`-o cache_dir=.venv/pytest-cache`, with the virtual environment first on PATH.
Local skips are not success evidence for their skipped behavior. Remote results
must be attributed to their actual run and revision, not inferred from this run.

One fresh read-only review reproduced four consequential problems: ignored
subscription matchers, absent session scope, unpaired post-events and quoted
interpreter checks. Each correction has a regression watched red then green.
Further controls cover concurrent duplicate posts, execution-directory mismatch,
pending-history eviction, before-completion coverage and bounded host identifiers.
No review issue was silently deferred. Authentication, competing writers and
unrelated tool side effects remain the explicit limits of target observation.

## Real project and installed host

The acceptance project is Snag (`E:\snag`); runtime modules contain no Snag path
or command rule. Four unrelated manifest families are exercised independently.
The project's own manifest discovered tests `npm run ci`, typecheck, build and
lint. Source selection was complete at 4,418 files / 81,841,401 bytes before
setup and 4,417 files / 81,841,184 bytes afterward. These are point-in-time
selection counts, not complete fingerprint or latency guarantees.

Project setup merged Claude and Codex wiring while preserving the existing local
permissions. A real **Claude Code 2.1.281** interactive session launched with local
settings, no external MCP configuration and no prompt. Its native SessionStart
callback was received and processed; the session then exited. This establishes
installed startup delivery, not an agent patch outcome or native CI capture.
Claude readiness reports active; Codex remains waiting. No Snag source or branch
was changed.

The actual external `npm run ci` exited **1**, with **14/15 checks passing**.
The sole failed check was production dependency audit: electron, mailparser,
next, nodemailer and undici had five unexcused high-or-critical package findings.
The gate was not bypassed or allowlisted. A diagnostic native-launcher relay used
the actual output and known exit status, explicitly with `--replay`; it persisted
a declared **complete/fail** receipt with no source coverage issues and kept
Codex activation waiting. The report labels freshness unchecked until evaluated.

Four added-host installed sessions, full native command capture and ordinary
working-session latency remain open. Snag's audit remediation belongs to that
project and was not part of this runtime delivery.

## Ten delivery parts

1. Unified five-host setup, activation and readiness (`cf94fa1`).
2. Targeted native content observations (`5ab63eb`).
3. Review corrections, missing-event and durable coverage handling (`13c7ab9`).
4. Generalized manifest and concurrent-project controls (`5858e79`).
5. Installation, commands and recovery guide (`359b431`).
6. Platform contracts and local state limits (`8348286`).
7. Rendered architecture (`7e6f741`).
8. Status, PLAN, roadmap and postponed scope (`9a686d7`).
9. Journey, development workflow and standing project-independence instruction (`be245da`).
10. README consistency and final validation record (`02d1286`).

All ten actual pushes succeeded. The first nine published incrementally on
`codex/live-onboarding`; the tenth atomically published that branch and main at
`02d12869724ae2925cf5dfb7cc9d90a70899b81f`. The [remote test matrix](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/36863821822)
completed successfully on Ubuntu and Windows with Python 3.11 and 3.13.
