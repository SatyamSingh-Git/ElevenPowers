# Configuration

[← The Guide](README.md)

Everything here is optional. **A project with no config file behaves exactly as it did before** — configuration exists to correct the runtime, not to be a prerequisite for it.

---

## The file

`.elevenpowers/config.json`, in your project root:

```json
{
  "profile": "strict",
  "commands": {
    "tests": "make test",
    "typecheck": "npm run typecheck",
    "build": "npm run build",
    "benchmark": "python bench.py"
  }
}
```

Two settings. Both matter, and the second one matters more than it looks.

---

## `profile` — how much it is allowed to interrupt

| Profile | Behaviour |
|---|---|
| `off` | record evidence, say nothing, never block |
| `guide` | say what would prove the work, report at the end, never block |
| `strict` | all of the above, and refuse to stop while obligations are unmet |

Default is `strict`.

Override for a single session without touching the file:

```bash
EP_PROFILE=guide claude
EP_PROFILE=off claude
```

### Which one do you want?

**`strict`** if the repository has a real test suite and you want the gate to do its job. This is the intended mode.

**`guide`** if you want the information without the interruption — a good first week, and the right setting for a repository whose suite is slow or partial. You still see what the work would need; you are simply not stopped.

**`off`** for a repository with no tests, for exploratory work, or when you want evidence quietly accumulating without the runtime ever speaking. Everything is still recorded, so `ep_status` still works.

---

## `commands` — how your project actually runs its checks

This is the single highest-value line of configuration, and it is worth understanding why.

Without it, the runtime has to infer that your project has a test suite by scanning for one. That fails in two directions: a suite hidden behind a `Makefile` or a task runner is invisible to a scan, and a guessed hint can name a command that does not exist.

With it, three things change:

1. **The runtime knows the suite exists**, even when nothing on disk looks like one.
2. **Hints name your real command** rather than a plausible-looking guess.
3. **The runtime discharges obligations by running the command itself** instead of interrupting to demand that the agent run it.

That third one is not a small convenience. It took live blocking from **75% of runs down to 12%** — the gate used to stop nearly every first attempt to finish, and nearly always on work that was already correct, because the agent had done the job and simply not shown it. Now the runtime goes and checks.

### Keys

Command keys match the obligation they satisfy:

| Key | Satisfies |
|---|---|
| `tests` | "the related test suite passes", "a test covering the change passes" |
| `typecheck` | "typecheck passes" |
| `build` | "the build succeeds" |
| `benchmark` | "a benchmark supports the improvement" |

Declare only what you have. An undeclared key simply falls back to the previous behaviour for that obligation.

### Examples

**Python, pytest:**
```json
{"commands": {"tests": "python -m pytest -q"}}
```

**Node, with a typechecker:**
```json
{"commands": {"tests": "npm test", "typecheck": "npm run typecheck", "build": "npm run build"}}
```

**Behind a Makefile — the case scanning cannot solve:**
```json
{"commands": {"tests": "make test", "build": "make"}}
```

**Quiet mode on a repository with no suite:**
```json
{"profile": "off"}
```

---

## What obligations each claim carries

Claims are inferred from your request by pattern matching — no model call, no added latency. Risk comes from the paths a task touches: anything under `auth/`, `payments/`, migrations, infrastructure or secrets is high risk and carries more. Everything else is scored by size.

| Claim | Low risk | High risk adds |
|---|---|---|
| `bug_fixed` | covering test passes, suite green | prior failure on record, stability over repeated runs |
| `feature_added` | suite green | covering test, typecheck, build |
| `refactor_safe` | suite green | typecheck, build |
| `migration_safe` | applies and reverts | suite green, stability |
| `perf_improved` | benchmark | suite green, stability |
| `deps_updated` | suite green | build, typecheck |
| `docs_changed` | nothing | nothing |
| `cannot_complete` | a reason and what was tried | evidence the blocker is real |

`cannot_complete` is a real outcome, not a failure. A system with no way to say *"this should not be done as asked"* reproduces the action bias that causes false completion in the first place.

---

## The four states

| State | Meaning |
|---|---|
| `VERIFIED` | every obligation met by fresh evidence |
| `UNVERIFIED` | an obligation has no evidence |
| `STALE` | evidence exists, but the files it observed have changed |
| `CONTRADICTED` | the latest evidence for something is failing |

A failure that was later fixed is *reproduction evidence*, not a contradiction — that is the point of asking for the failing test first. Only the most recent record per identity counts.

---

## Version control

Add this to `.gitignore`:

```
.elevenpowers/ledger.json
.elevenpowers/blindspots.jsonl
```

`config.json` is worth committing — it is a statement about how your project is built, and everyone on the team benefits from it. The ledger and the blindspots file are machine state and should not be.

To ignore the whole thing:

```
.elevenpowers/
```

---

Questions, or a configuration case this does not cover? **[satyambcnrk@gmail.com](mailto:satyambcnrk@gmail.com)**
