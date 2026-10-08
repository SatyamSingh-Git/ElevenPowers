# Verification across development milestones

The [two-stage subscription comparison](preservation-comparison.md) exercises
this workflow with identical ordinary/assisted inputs and independent checks.
Its [first four sessions](../results/behavior-preservation/README.md) tied on
correctness; current completion receipts did not establish exact-command native
capture or a coding-quality benefit. Advice remains explicit project opt-in.

Milestones keep earlier behavior checks visible when development moves to a new
task. They are optional, project-owned and shared by all five host integrations.
Their evidence is separate from the current task's claims and completion verdict.

Qualified [literal command wrappers](command-capture.md) retain the exact
configured check identity across tasks. A later failed or incomplete invocation
supersedes earlier success for that check; the raw invocation remains provenance.
Changed declarations still stale earlier receipts, and targeted test scope stays
separate from whole-suite evidence.

Create a tracked `elevenpowers.milestones.json` at the project root:

```json
{
  "schema": 1,
  "milestones": [{
    "id": "authentication",
    "description": "A valid session permits the authenticated request.",
    "inputs": ["src/auth.py", "tests/test_auth.py", "requirements.txt"],
    "checks": [{"kind": "test_suite", "command": "python -m pytest tests/test_auth.py"}]
  }]
}
```

Choose existing files and the exact command your host captures. Include the
behavior's production files, tests, configuration and dependency declarations.
Use `/` in paths on every OS. Inputs must be ordinary normalized relative files;
links, nested Git repositories, `.git` and `.elevenpowers` paths are refused.
Missing inputs remain explicit gaps. Descriptions express your expectation;
ElevenPowers does not infer a correctness specification from them.

The check kinds are `test_suite`, `build`, `typecheck`, `lint` and `benchmark`.
These declarations neither discover commands nor execute them. Use a supported
producer, or an existing project-configured command for an opaque wrapper. A
different spelling, wrapper or argument list does not match the exact identity.
Unsupported producers leave evidence absent. See [command configuration](configuration.md).

Once the file is present, ordinary captured receipts are retained automatically
by the existing atomic ledger save. No new host setup is required. The latest
aggregate receipt for each kind/command survives a new task without supplying
evidence for that task's claims. Older passes cannot hide later failures or
incomplete attempts. Historical input fingerprints remain unchanged.

Inspect the project explicitly:

```bash
python plugin/bin/ep_milestones.py --project PATH
python plugin/bin/ep_milestones.py --project PATH --json
python plugin/bin/ep_milestones.py --project PATH --impact --changed src/auth.py
python plugin/bin/ep_milestones.py --project PATH --check
```

Inspection launches no project checks, models, installer or host, and creates
no project state. The shared scanner may run bounded Git metadata commands.
`--seconds` is a cooperative budget from 0 to 120, default 30. `--output FILE`
exports explicitly; `--force` authorizes overwrite. Ordinary report exit 0
means a report was produced. `--check` exits 1 unless the whole milestone view
is `CURRENT` with complete requested coverage. Invalid invocation/export exits 2.

| State | What it establishes |
|---|---|
| `CURRENT` | A complete passing command with fresh observations covering the declared inputs and declaration file |
| `FAILED` | A fresh complete failing execution |
| `STALE` | A prior execution whose observed inputs are no longer current |
| `INCOMPLETE` | Incomplete execution, invalid metadata, missing inputs or unresolved coverage |
| `ABSENT` | No matching receipt has been recorded |

The report preserves result, execution and freshness separately. An old failure
after another source edit is stale; it is not a fresh diagnosis of today's code.
Incomplete, failed, stale and absent take precedence over current when combining
checks. A passing suite that counted zero tests cannot qualify. An opaque passing
command is explicitly qualified at command level, without counted assertions.

Every qualifying receipt must cover the declaration file and **all** declared
inputs. Editing the expectation or its scope therefore requires fresh evidence.
Native source-scoped receipts retain whole-source invalidation: even an unrelated
selected-source edit can expire them. Writing fewer paths in the milestone file
does not narrow an existing receipt. Explicit-path receipts can remain current
after unrelated edits only when their actual producer observed the entire declared
scope. Unrecorded dependencies, external services and environment remain unknown.

`--impact` adds explained direct/dependency leads from a fresh ImpactGraph. With
no `--changed`, it uses current task touched paths as observations. No available
change observation or a graph budget gap stays incomplete. A missing path never
certifies unaffected behavior or authorizes omitting fallback checks. Advice
does not change an individual command's evidence state. Optional bounded edit
advice is available below; new milestone completion blockers remain outside this release.

`ep_report.py` adds the section only for opted-in projects, while retaining the
current task's own verdict. History strips captured output/details, retains at
most 256 command identities within 4 MiB and reports omissions. The report reads
at most 8 MiB of ledger JSON; declarations are limited to 128 KiB, 64 milestones,
128 inputs and 16 checks each. Invalid declarations fail closed. Budget/eviction
diagnostics persist; a missing historical attempt cannot be assumed passing.
Temporary declaration errors recover after the file is repaired and fresh
matching observations are captured. Unknown history gaps require new observations
covering every currently declared check and its inputs; re-saving old receipts
does not clear them. New corruption/eviction reopens that recovery requirement.
Deleting the declaration stops new milestone capture and preserves the archive.

Receipts are unsigned local observations, not independent attestations or proof
of universal safety. Collection detects declaration/ledger movement but is not
an atomic filesystem transaction. This release adds a useful inspection and
retention capability; coding improvement still needs a controlled usage result.

## Optional automatic edit advice

After declaring milestones, add this to the existing `.elevenpowers/config.json`:

```json
{"milestone_advice": {"enabled": true, "seconds": 1, "cooldown": 30, "max_attempts": 3}}
```

Preserve your other configuration fields. All five hosts use the same saved-edit
boundary. Advice appears after an observed edit and contains exact declared check
previews, evidence states and direct/dependency/fallback reasons. It runs no
checks, model or installer and adds no completion blocker. Off stays silent.
Install/setup alone does not enable this optional experiment.

Inspection runs in an isolated Python worker with a one-second cooperative report
budget plus a 0.5-second process grace. Set `seconds` between 0.1 and 5,
`cooldown` between 0 and 3600, and integer `max_attempts` between 1 and 10.
Defaults are shown above. Bounds limit work, not overall OS/host latency.
Repeated observations are suppressed, including failed attempts; content
metadata changes can request another attempt after cooldown, up to the task cap.
New tasks receive their own allowance. Stat metadata is only a dedup hint;
existing content fingerprints still determine evidence freshness.

The ignored `.elevenpowers/advice.json` retains reservations, digests, counters,
timings and delivery outcomes for up to 20 tasks, never evidence or transcript
text. Reservations are saved before work, so an interrupted worker consumes an
attempt rather than silently launching again. Delivered advice can still have
incomplete coverage. Corrupt/linked state declines work with a diagnostic.
The full explicit report remains available after a timeout, cooldown or cap.

Context shows at most six commands, three reasons each and 6000 characters;
omissions and truncated previews are labelled. Keep omitted/fallback checks.
For process launches, use [declared file relationships](impactgraph.md#query-before-editing).
Larger-project precision and installed edit-session cost remain unqualified;
see [actual measurements](../results/milestone-advisories/README.md) and
[launcher/native distinctions](../results/milestone-advisories/callbacks.md).

For a disposable exercise with real checks:

```bash
python -m eval.milestones --output NEW_DISPOSABLE_DIR
```

The destination must not exist. The controller writes fixed provider, checkout
and worker expectations, then runs actual pytest and optional Node checks through
later faults, repairs, equivalent behavior and scope controls. It keeps logs,
fingerprints and every attempted outcome. It launches no model. These authored
controls establish capability, not installed-host acceptance or a coding-benefit
comparison. See [published observations](../results/milestone-verification/README.md)
and [the design](../docs/design/milestone-verification.md).

## Explained exact rechecks

With `--impact`, JSON adds `rechecks` schema 1 and Markdown shows a recommended
order. Each kind/exact-command identity appears once, retaining all associated
milestones and their CURRENT/FAILED/STALE/INCOMPLETE/ABSENT states. No command is
invented from filenames or prose. Refresh-needed commands come first, then:

| Priority | What the report observed | What it does not establish |
|---|---|---|
| direct | A changed path is a declared milestone input | That the behavior is broken |
| dependency | A current graph witness reaches a declared input | Actual assertion coverage or a failure probability |
| fallback | No available witness reaches the declared inputs | That the milestone is unaffected or safe to skip |

`needs_refresh` comes from evidence state, separately from priority. A shared
command needs refresh if any associated check is not CURRENT. Current rows remain
visible. Incomplete report coverage must be resolved before relying on the list.
Source movement between graph/evidence snapshots, omitted explanations and graph
budgets stay explicit and prevent a complete requested gate. Original graph
fingerprints remain distinct from comparable evidence content identities.

The limits are 1,024 exact check identities, 64 milestone references per identity,
16 reasons per command and 256 change observations/leads. Extra observations and
reasons are counted/reported. Direct matches survive graph deadline exhaustion;
fallback commands remain even when no graph advice can finish. Graph/query/ranking
times are descriptive local observations. Inspection executes no project command.

For independent local controls, explicitly run:

```bash
python -m eval.milestone_rechecks --output NEW_DISPOSABLE_DIR
```

This creates fixed authored projects and executes Python/pytest and optional Node
checks. It records misses, unrelated/equivalent behavior, all attempts and paired
read cost. Missing Node is incomplete, not a passing Node case. See
[results](../results/milestone-rechecks/README.md) and
[design](../docs/design/milestone-rechecks.md). Automatic hooks, narrow native
receipts and an agent-benefit comparison remain separate milestones.
