# The Guide

Everything you need to install ElevenPowers, run it, understand what it is telling you, and get unstuck.

If something here is wrong, out of date, or simply does not work — **[satyambcnrk@gmail.com](mailto:satyambcnrk@gmail.com)**, or open an issue on [the repository](https://github.com/SatyamSingh-Git/ElevenPowers/issues). A report that says "I ran X, expected Y, got Z" is worth more than a polite one.

---

## Start here

| | |
|---|---|
| **[installation.md](installation.md)** | requirements, install, and how to prove it actually loaded |
| **[platforms.md](platforms.md)** | all five hosts, native setup/removal, bundles and per-platform validation limits |
| **[commands.md](commands.md)** | every command, every flag, and what the output means |
| **[configuration.md](configuration.md)** | automatic setup, command overrides, scan budgets and profiles |
| **[troubleshooting.md](troubleshooting.md)** | what goes wrong, why, and the fix |

---

## Claude Code quick start

```bash
git clone https://github.com/SatyamSingh-Git/ElevenPowers.git
claude --plugin-dir ElevenPowers/plugin
```

That loads the Claude Code integration. For Codex, Gemini CLI, Cursor Agent or GitHub Copilot CLI, follow [native platform setup](platforms.md). Once the chosen host loads and trusts the hooks, supported startup, observation and completion work runs automatically.

Then, from inside a project:

```bash
python ElevenPowers/plugin/bin/ep_doctor.py    # is the runtime actually hearing the host?
python ElevenPowers/plugin/bin/ep_status.py    # what does this task still owe?
```

Check the doctor's reported results rather than a fixed line count. For the four additional hosts, use `ep_doctor.py --platform PLATFORM --cwd PATH`; this checks configuration and launcher availability, not live delivery. See [troubleshooting.md](troubleshooting.md) for failures.

For any of the five hosts, `ep_setup.py HOST --project PATH` installs reversible
project wiring and prints readiness. `ep_ready.py HOST --project PATH` reports
activation, effective commands, environment/coverage issues and next actions.
Each project supplies its own manifests and overrides. See [installation](installation.md)
for auto selection and removal.

Readiness now checks the complete staged pipeline with fresh input evidence,
retained timing samples and optional-engine metadata. Use `--check` when you want
an exit-code gate; ordinary reads remain diagnostic. To validate a host version,
use the explicit disposable Python/JavaScript exercise in [commands](commands.md#ep_doctor--repeatable-native-acceptance).
Preparation never launches an agent, and replay never counts as native acceptance.

For a report another person can read, use
`ep_report.py --project PATH --output report.md`, or add `--format json`.
It shares the same ledger across all five hosts and reads current input content
without rerunning checks. See [commands](commands.md#ep_report--evidence-to-share-with-a-reviewer)
for coverage, privacy, deadline and exit-status details.

Reports also show optional changed-file test strength: engine-generated changes
detected or missed by passing tests. After explicit engine setup, completion
considers the bounded shared runner automatically. Use `ep_strength.py --root PATH`
for an explicit run and [configuration](configuration.md) for focused commands and
limits. Findings are qualified human observations and do not change the verdict.

---

## What you should expect to see

Nothing at all, most of the time. Ask a question, request a code read, or make a documentation change and the runtime stays entirely out of the way — no claim opens, nothing is said.

When the agent starts editing source, a claim opens, and you will see the obligations once, at the first edit:

```
this task will need, before it can be called done:
  a test covering the change passes
    run the test that exercises this change, by name or by file
  the related test suite passes
    run the suite covering the files you changed, not just the one test
```

When the agent tries to finish, the gate computes a state rather than accepting the claim:

```
UNVERIFIED  bug_fixed
  missing  a test covering the change passes
           run the test that exercises this change, by name or by file
  met      the related test suite passes
```

On the default `strict` profile, an `UNVERIFIED` claim stops the turn and the agent goes back to work. On `guide` it is reported and the turn ends normally. On `off` evidence is still recorded, silently.

---

## Where this is worth using

**Good fit.** A repository with a real test suite, where "done" is expensive to get wrong — a bug fix that must not regress something else, a change under `auth/`, `payments/`, a migration, anything where you would normally re-check the agent's work by hand. It is most useful precisely where you are least able to eyeball the diff.

**Good fit.** Intermittent and flaky failures. This is the one case where a single green run proves nothing, and it is the case nothing else in the field tools at all. See `ep-repeat` in [commands.md](commands.md).

**Poor fit.** A repository with no tests. The gate can only compute from evidence that exists; with no suite to run, most obligations have no way to be met and you will be interrupted for something you cannot supply. Use `profile: "guide"` or `"off"` there.

**Poor fit.** Exploratory or throwaway work, prototypes, spikes. Set `profile: "off"` and let it record quietly, or do not install it on that project.

**Currently untested.** Very large repositories. Invalidation is coarse today — any source edit stales every piece of evidence — so on a big tree you may find things going `STALE` more often than is useful. That is a known limitation with a documented trigger for fixing it; see [whats-offered/roadmap.md](../whats-offered/roadmap.md).

---

## An honest note on maturity

This is early software. The plugin discovers supported project commands, reports startup health, captures evidence and runs missing checks at completion. Dated [validation records](../docs/validation/README.md) distinguish full runs from targeted reruns; `python -m pytest tests -q` is the authority for the current checkout. What has **not** been established is whether work produced with the gate on is actually better than work produced without it — that measurement is still open, and the project says so in its own [README](../README.md) and [PLAN.md](../PLAN.md).

So: use it, and tell me when it is wrong. Bug reports are the most valuable thing anyone can send right now.

**[satyambcnrk@gmail.com](mailto:satyambcnrk@gmail.com)**

## Dated native validation and performance

Use `ep_validate.py` explicitly to capture current disposable acceptance, build a
ten-cell host/language matrix, or sample read-only health costs. Software content
identity now binds preparation and real startup; a runtime update needs a new
exercise. Installed versions are observed only with `--observe-version`. Saved
reports describe their creation time. Missing hosts and native trust gaps remain
visible. See [commands](commands.md) and [the dated delivery](../docs/validation/2026-10-02-native-validation.md).

The explicit subscription pilot compares identical frozen coding tasks with
independent grading. Installation never starts it. Its first eight records were
inconclusive because native execution/activation and subscription quota blocked
the comparison; they do not establish better coding.


Archived comparisons can be inspected against their recorded protocol after
evaluator updates. The current evaluator separates behavioral execution from
final assertions and supports normal package imports. Its sixteen checks remain
a bounded sample; passing them does not mean every requirement is covered.
