# The Guide

Everything you need to install ElevenPowers, run it, understand what it is telling you, and get unstuck.

If something here is wrong, out of date, or simply does not work — **[satyambcnrk@gmail.com](mailto:satyambcnrk@gmail.com)**, or open an issue on [the repository](https://github.com/SatyamSingh-Git/ElevenPowers/issues). A report that says "I ran X, expected Y, got Z" is worth more than a polite one.

---

## Start here

| | |
|---|---|
| **[installation.md](installation.md)** | requirements, install, and how to prove it actually loaded |
| **[commands.md](commands.md)** | every command, every flag, and what the output means |
| **[configuration.md](configuration.md)** | profiles, declaring your test commands, turning it down or off |
| **[troubleshooting.md](troubleshooting.md)** | what goes wrong, why, and the fix |

---

## Sixty seconds to running

```bash
git clone https://github.com/SatyamSingh-Git/ElevenPowers.git
claude --plugin-dir ElevenPowers/plugin
```

That is the whole install. There is nothing to configure, no account, no key, and no network call. Ask your agent for a change the way you normally would.

Then, from inside a project:

```bash
python ElevenPowers/plugin/bin/ep_doctor.py    # is the runtime actually hearing the host?
python ElevenPowers/plugin/bin/ep_status.py    # what does this task still owe?
```

`ep_doctor` should print six green lines. If it does not, go straight to [troubleshooting.md](troubleshooting.md) — everything else depends on that layer working, and its failure mode is silence rather than an error.

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

This is early software. The plugin installs, captures evidence, discharges declared commands and reports, and the suite covering it is green — `python -m pytest tests -q` is the authority, not a number written on a page. What has **not** been established is whether work produced with the gate on is actually better than work produced without it — that measurement is still open, and the project says so in its own [README](../README.md) and [PLAN.md](../PLAN.md).

So: use it, and tell me when it is wrong. Bug reports are the most valuable thing anyone can send right now.

**[satyambcnrk@gmail.com](mailto:satyambcnrk@gmail.com)**
