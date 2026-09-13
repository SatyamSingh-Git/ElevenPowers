# Troubleshooting

[← The Guide](README.md)

Start every investigation the same way:

```bash
python plugin/bin/ep_doctor.py --host
```

Six green lines means the runtime is hearing the host correctly and your problem is elsewhere in this page. Anything else, fix that first — nothing downstream works if this layer is broken, and **its failure mode is silence, not an error**.

---

## The runtime says nothing at all

By far the most common report, and it has an innocent explanation more often than not.

**It may be correct.** Ask a question, request a code read, or change only documentation, and no claim opens. The runtime deliberately stays out of the way. Confirm with `ep_status.py` — if it reports no open claim after an actual source edit, keep reading.

**Check the plugin actually loaded.** `--plugin-dir` has to point at [`plugin/`](../plugin/), not at the repository root:

```bash
claude --plugin-dir ElevenPowers/plugin     # correct
claude --plugin-dir ElevenPowers            # wrong, loads nothing
```

**Check the subscriptions.** If `ep_doctor` reports a drifted subscription:

```bash
python -m core.wiring
```

**Check your profile.** `profile: "off"` records silently by design. So does `EP_PROFILE=off` left over in your environment:

```bash
echo $EP_PROFILE        # bash
echo $env:EP_PROFILE    # PowerShell
```

---

## `ep_doctor` fails a line

### `FAIL  python 3.x`

Python 3.11 or later is required. If you have a newer Python that Claude Code is not using, the hook runs whatever `python` resolves to on the host's `PATH`, which may not be the interpreter you tested with. Check with:

```bash
python --version
```

### `FAIL  a failing command is recorded as failing`

The most serious one. It means the host's failure shape is not being recognised, so **every failing command is being recorded as a pass** — a gate that verifies everything. This exact defect shipped once and survived 119 passing unit tests.

Usually a Claude Code version whose payload shape has changed. Run `ep_doctor.py --host` for the fuller check, then send me the output — this is worth an immediate fix on my side, not a workaround on yours.

### `FAIL  hooks.json subscribes to every event the runtime handles`

```bash
python -m core.wiring
```

Rewrites the subscription file. Re-run `ep_doctor` to confirm.

### `FAIL  the ledger directory is writable`

The runtime cannot create or write `.elevenpowers/` in your project. Check permissions on the project directory; on Windows check that the folder is not marked read-only and that a security tool is not locking it.

### `FAIL  nothing unreadable has arrived from the host`

Something came from the host that the runtime could not parse, and it was appended to `.elevenpowers/blindspots.jsonl` rather than silently dropped. That file **is** the diagnosis:

```bash
cat .elevenpowers/blindspots.jsonl
```

This is the designed behaviour for a host that changes a field — it becomes a diagnosable symptom instead of a tool that quietly went quiet. Please send me the file; that is exactly what it is for.

### `unknown option(s): --whatever` (exit 2)

`ep_doctor` refuses flags it does not know rather than ignoring them. Known flags are `--cwd` and `--host`. This strictness exists because the script once accepted `--host` silently and printed six green lines about something else entirely.

---

## I am blocked and cannot finish

The `strict` profile refuses to stop while obligations are unmet. That is the point, but you are allowed to overrule it.

**For one session:**
```bash
EP_PROFILE=guide claude
```

**For the project**, in `.elevenpowers/config.json`:
```json
{"profile": "guide"}
```

**Then ask why it blocked.** `ep_status.py` shows exactly which obligation has no evidence. In the great majority of cases the work was already done and simply not shown — which is why declaring your commands matters:

```json
{"commands": {"tests": "make test"}}
```

With that, the runtime runs the suite itself and computes the evidence instead of interrupting to demand it. This one change took live blocking from 75% of runs to 12%.

---

## Everything keeps going `STALE`

Known limitation, honestly documented. Invalidation is **coarse** today: any source edit stales every piece of evidence, rather than only the evidence whose files actually changed.

On a small project this is barely noticeable. On a large one it can be tiresome, and the fix — narrowing the observed set to the import closure of each test — is written down with a trigger in [`docs/postponed.md`](../docs/postponed.md). The trigger is exactly this complaint being measured in real use.

**So please report it.** "This is annoying on my repository of N files" is the measurement that starts that work. Until then, `profile: "guide"` removes the interruption while keeping the information.

---

## The hint names a command that does not exist

The runtime guessed, and guessed wrong. Tell it the truth:

```json
{"commands": {"tests": "pnpm vitest run", "typecheck": "pnpm tsc --noEmit"}}
```

See [configuration.md](configuration.md). Guessed hints were a real defect; declaring commands is the cure.

---

## `ep-repeat` says "no command given; put it after --"

The command goes after a bare `--`:

```bash
python plugin/bin/ep_repeat.py 50 -- pytest tests/test_login.py     # correct
python plugin/bin/ep_repeat.py 50 pytest tests/test_login.py        # wrong
```

The separator exists so that `ep-repeat`'s own flags are never swallowed into the command being repeated.

---

## Results differ between machines, or between me and CI

Check your Git line-ending configuration before anything else:

```bash
git config core.autocrlf
```

This is not paranoia. In a ninety-run measured sweep on this project, **the grade turned out to be a function of the grader's Git configuration** — a checkout under one `core.autocrlf` setting produced different results from the same commit checked out under another. It cost real money to discover and it is written up in [journey/23-spend.md](../journey/23-spend.md).

If you are comparing results across machines, pin the setting on both.

---

## The Stop hook feels slow

The `Stop` hook has a 600-second timeout because it may run your declared test suite. Every other hook is capped at 20 seconds. If stopping is slow, the runtime is almost certainly running your suite — which is the behaviour that replaced interrupting you to ask for it.

If your suite is too slow to sit inside a turn, either declare a faster subset:

```json
{"commands": {"tests": "python -m pytest tests/unit -q"}}
```

or switch to `profile: "guide"`, where the suite is not run and you are told what would prove the work instead.

---

## Something else, or something here did not help

Please get in touch. Early software with few users means your bug report is likely the only one, and I would much rather hear about it than not.

**[satyambcnrk@gmail.com](mailto:satyambcnrk@gmail.com)** · [GitHub issues](https://github.com/SatyamSingh-Git/ElevenPowers/issues)

Include, if you can:

```bash
python plugin/bin/ep_doctor.py --host      # the output of this
python --version                            # and this
```

plus your OS, your Claude Code version, and what you expected to happen versus what did. If `.elevenpowers/blindspots.jsonl` exists, attach it — that file exists precisely so this conversation can be short.
