# Installation

[← The Guide](README.md)

---

## Requirements

| | |
|---|---|
| **Python** | 3.11 or later. `ep_doctor` checks this first and fails loudly if not |
| **Host** | [Claude Code](https://claude.com/claude-code). It is the only host wired today — a second adapter is postponed with a trigger, see [roadmap](../whats-offered/roadmap.md) |
| **Git** | used to identify the state of the working tree when evidence is recorded |
| **Network** | none. Nothing here calls out, no key, no account, no telemetry |
| **Dependencies** | none beyond the Python standard library. One *optional* extra is described below |

Works on Windows, macOS and Linux. It is developed on Windows, so the Windows paths are the best-tested ones — which is unusual enough to be worth saying.

---

## Install

```bash
git clone https://github.com/SatyamSingh-Git/ElevenPowers.git
claude --plugin-dir ElevenPowers/plugin
```

That is all of it. No build step, no `pip install`, no configuration file required.

The `--plugin-dir` flag points Claude Code at [`plugin/`](../plugin/), which contains a manifest, a hook subscription file, and four small entry points. Everything else is imported from `core/` next to it.

### Making it permanent

Passing `--plugin-dir` every time gets old. To load it for every session, add the plugin directory to your Claude Code settings rather than the command line — see the Claude Code documentation for plugin configuration on your version. If you get this working in a way worth documenting, please send it to me and it will go in this file with credit.

---

## Optional: other languages

Everything works on any repository out of the box. One feature is **Python-only until you opt in**: the blast radius, which names the other implementations and callers of whatever you just changed. It needs to understand inheritance, and Python's standard library can only parse Python.

```bash
pip install tree-sitter-language-pack
```

That adds **TypeScript, TSX, JavaScript, Go, Rust, Java, Ruby, PHP and C#**. Nothing else changes, and there is no configuration — the feature notices the pack and starts reading those files.

Without it, nothing breaks and nothing is silently degraded: Python is read exactly as before through the standard library, other languages are simply not read, and the check says nothing rather than guessing. That is why it is optional at all — a plugin you must install four packages to try is a plugin nobody tries.

This is the same approach Aider, Continue and OpenCode use, for the same reason: parsing many languages accurately means tree-sitter, and there is no lighter answer that is still correct.

---

## Prove it actually loaded

This matters more than it sounds. The layer between this runtime and its host has failed three times in this project's history, and **every one of those failures looked like silence** — no error, no crash, unit tests all green, and the runtime simply recording nothing. So there is a command whose entire job is to catch that:

```bash
python ElevenPowers/plugin/bin/ep_doctor.py
```

You want six green lines:

```
ok    python 3.13.2
ok    a failing command is recorded as failing
ok    a passing command is recorded as passing
ok    hooks.json subscribes to every event the runtime handles (7 tools recorded)
ok    the ledger directory is writable (/path/to/your/project/.elevenpowers)
ok    nothing unreadable has arrived from the host
```

It exits non-zero when something is wrong, so it drops straight into CI.

For a deeper check that drives the launcher as a real process with a real payload on stdin — rather than calling the reader inside the same interpreter — add `--host`:

```bash
python ElevenPowers/plugin/bin/ep_doctor.py --host
```

> [!NOTE]
> `--host` is worth running at least once after install. It exists because the shallower check passed for weeks while quietly discarding the flag, which is a passing check that means nothing. If the two disagree, trust `--host`.

Any line that is not `ok` is covered in [troubleshooting.md](troubleshooting.md).

---

## What gets written where

Everything the runtime stores lives in one directory inside your project:

```
your-project/
└── .elevenpowers/
    ├── ledger.json          the evidence records for this project
    ├── blindspots.jsonl     anything arriving from the host that could not be read
    ├── config.json          yours, optional — see configuration.md
    └── .gitignore           written by the runtime: `*`
```

Nothing is written outside your project directory. Nothing is sent anywhere.

**You do not need to add anything to your `.gitignore`.** The directory ignores itself — the runtime writes a `.gitignore` containing `*` into it on every save, which git honours whatever your own ignore file says, so `git add -A` cannot pick it up. The ledger holds your prompts, the commands that ran and a bounded amount of what they printed; that is machine state and it should not be in your history. If you put your own `.gitignore` there, it is left alone.

Credentials are stripped from captured output before it is written — issuer prefixes, named values like `AWS_SECRET_ACCESS_KEY=`, bearer headers, JWTs and private-key blocks. See [features.md](../whats-offered/features.md) for what that does and does not cover.

If you *want* something in there committed, edit that `.gitignore` rather than deleting it — deleting it only means the runtime writes it again on the next save, while a file that is already there is never touched. `*` then `!config.json` on the next line commits your configuration and nothing else.

---

## Which events it subscribes to

For reference when debugging — this is [`plugin/hooks/hooks.json`](../plugin/hooks/hooks.json):

| Event | Why |
|---|---|
| `SessionStart` | pick up an existing task on startup, resume, or after compaction |
| `UserPromptSubmit` | decide whether the request opens a claim |
| `PreToolUse` | the scope guard, before an edit lands |
| `PostToolUse` | read the result of a command and file it as evidence |
| `PostToolUseFailure` | the failure shape the host sends separately — missing this one was a real defect |
| `Stop` | compute the state and, on `strict`, refuse the stop |

If `ep_doctor` reports a drifted subscription, `python -m core.wiring` rewrites the file.

---

## Uninstalling

Stop passing `--plugin-dir` (or remove it from your settings), and delete `.elevenpowers/` from any project you used it in. There is nothing else — no global state, no registry entries, nothing in your home directory.

---

## Trouble?

[troubleshooting.md](troubleshooting.md) first. If that does not cover it: **[satyambcnrk@gmail.com](mailto:satyambcnrk@gmail.com)** or [an issue](https://github.com/SatyamSingh-Git/ElevenPowers/issues). Include the output of `ep_doctor.py --host`, your Python version, and your OS — that triple resolves most of it immediately.
