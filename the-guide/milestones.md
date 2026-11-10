# Verification across development milestones

[Owned declared checks](declared-checks.md) feed the existing cross-task history. A failed child remains failed even if its outer shell succeeds. The independent scoped consumer remains current after a different selected dependency changes. Owned configuration/producer association and source-byte freshness are separate qualifications.

Complete [command input scopes](external-inputs.md#command-specific-qualification) now qualify retained milestones independently. Drift in one selected dependency can stale its behavior check while an independent complete scope stays current. Missing provenance remains incomplete; source freshness is a separate fact.

The [two-stage subscription comparison](preservation-comparison.md) exercises
this workflow with identical ordinary/assisted inputs and independent checks.
Its [first four sessions](../results/behavior-preservation/README.md) tied on
correctness; current completion receipts did not establish exact-command native
capture or a coding-quality benefit. Advice remains explicit project opt-in.

Milestones keep earlier behavior checks visible when development moves to a new
task. They are optional, project-owned and shared by all five host integrations.
Their evidence is separate from the current task's claims and completion verdict.

Declared [external inputs](external-inputs.md) now qualify retained receipts too.
Selected dependency bytes can stale a passing behavior check without a source
edit or HEAD movement. `source_freshness` and `external_inputs` explain the
separate facts; old unpaired history and incomplete current access remain
`INCOMPLETE`. A fresh actual execution can recover `CURRENT`. Inspection and
recheck advice do not run the commands or exclude required checks.

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

## Rule groups: one rule kept in several files

A rule worked out in two places, such as a tax rounding or an overtime split,
breaks quietly when only one place changes. Twenty of the 31 losses in the
multi-stage v3 run were exactly this. Agents act on a rule you name, but the
proposals below did not find rules in real code, so name the ones you know.

### Mark it where it lives

The cheapest way is two comments. This is the convention Chromium,
TensorFlow and abseil already use, Google's IfThisThenThat, and it is read
here as [ifttt-lint](https://github.com/simonepri/ifttt-lint) reads it:

```python
# LINT.IfChange(upload_limit)
MAX_UPLOAD_SIZE_MB = 50
# LINT.ThenChange(//docs/api.md:upload_limit)
```

- **Before the first edit:** before an agent first edits
  `config/upload.py`, its brief says the block is also kept in
  `docs/api.md:upload_limit`. An agent that writes the file through a
  shell command gets the same note after that command.
- **At completion:** the end report names the block if the task changed a
  line inside it but not its target. With `"rule_gate": true` under
  `strict`, the agent is sent back once as well, as for a declared rule.
  - A `path:label` target counts as changed only if its labelled block
    changed.
  - A bare path counts if the file changed at all.
  - `:label` is a block in the same file.
- **Paths:** `//path` is read from the project root. Any other path is read
  from the file's folder, then from the root. A target that is not in the
  project, such as an internal path in exported code, is not put on the
  agent.
- **Comments:** `#`, `//`, `--`, `;`, `%`, `/* */` and `<!-- -->` all work.
  A directive must be alone on its comment line. Nested blocks, unclosed
  blocks and directives in Markdown fences are not read, and the listing
  names them.
- **What it does not do:** a marked rule carries no checks, and nothing
  blocks.
- **Projects that already mark rules** need nothing else.

```bash
python plugin/bin/ep_milestones.py --project PATH --marked
```

This lists every marked rule, with any target or label not found. On
abseil-py it lists two rules, on TFX 18 and on TF-GNN 26.

**Measured, and not:**
- **The note** uses the delivery and wording measured for declared rules
  (below).
- **Marking** is a new way into that note. It has not been measured with
  agents on its own.

### Rules other agents already have

If your project already has scoped rules written for another agent,
ElevenPowers delivers them to whichever agent is running. You do not need to
write anything new:

| Format | Read from | Scoped by |
|---|---|---|
| Claude Code | `.claude/rules/**/*.md` | `paths:` |
| Cursor | `.cursor/rules/**/*.mdc` | `globs:` (rules with `alwaysApply: true` are not scoped, and are left to Cursor) |
| GitHub Copilot | `.github/instructions/**/*.instructions.md` | `applyTo:` |
| `AGENTS.md` in a subfolder | that folder | the closest one to the file wins |

**When it arrives.** Before an agent first changes a matching file, the note
carries the rule's own text, cut to 600 characters, with its source named.
It arrives after the change on hosts that cannot take text before one (Cursor,
Copilot), and after a shell command that wrote the file.

**What is skipped.**
- At most two scoped rules are added per file.
- On an edit, a host is not handed its own format, because it loads that
  itself: Claude Code is not handed `.claude/rules`, Cursor not
  `.cursor/rules`, Copilot not its instructions. After a shell write nothing
  is skipped, because no host loads rules for a file a script wrote.
- A root `AGENTS.md` and rules without a scope are not repeated. Hosts load
  those at the start.

**Checked:** a real Claude Code session quoted a Cursor rule it had never
opened, and the same project without the rule got nothing
([probe](../results/scoped-rules/README.md)).

**Seeing what was found.** `ep_milestones.py --scoped` lists every rule found
and every file that could not be read; an unreadable rule is never delivered.

```bash
python plugin/bin/ep_milestones.py --project PATH --scoped
```

### Declare a rule in one line

```bash
python plugin/bin/ep_milestones.py --project PATH --add-rule src/money.py src/pricing.py --why "Both round tax half-up."
```

It writes an entry worded as the measured instruction, "`src/money.py` and
`src/pricing.py` must stay consistent: change both in the same task", with
the project's tests command as its check. It creates
`elevenpowers.milestones.json` if it is missing. It refuses:
- a missing file;
- the same file twice;
- a pair already declared;
- a project with no tests command.

### Or declare it, with a check

An entry in `elevenpowers.milestones.json` also carries the check that
proves the behaviour (above). The proposals help you think of entries. The
approach is borrowed from NVIDIA Auto-Ontology: a machine discovers
candidates, you certify them, and only what you certified reaches the
agent.

```bash
python plugin/bin/ep_milestones.py --project PATH --propose --limit 50
```

1. **Discover.** Each proposal names two files, the two functions, the rare
   words they share, and a milestone entry ready to edit. The words are the
   reason: shared `ROUND_HALF_UP`, `quantize` and `cents` suggest one rounding
   rule, while shared `writer` and `newline` are just two CSV writers. Pairs
   already declared or marked together are not proposed again.
2. **Certify.** Copy an entry you accept into `elevenpowers.milestones.json`,
   and keep or change its check. An entry needs at least one check. The
   project's declared `tests` command is filled in when there is one.
   - **The description is already an instruction**, for example:
     "`summarise` (…/month_end.py) and `_spent_by_category` (…/budgets.py)
     must stay consistent: change both in the same task." Keep that form if
     you reword it. Where a request pulled the other way, the dependent was
     left behind in 5 of 60 runs worded this way, against 23 of 60 with a
     plain description, with no needless edits (p = 8.3 × 10⁻⁵, one stage,
     Sonnet 5.5) ([results](../results/rule-mandate-confirm/README.md)).
   - Keep it under 200 characters: the note shows only the first 200.
3. **Ground.** Before an agent first edits a file in a declared rule that
   names other files, its brief says so and names them. An agent that writes
   the file through a shell command gets the same note right after that
   command. At completion, the end report names a declared rule the task
   changed in only some of its files. Neither blocks, unless you opt in:
   under `strict`, `"rule_gate": true` in `.elevenpowers/config.json` sends
   the agent back once at Stop, naming the rule and the unchanged files. It
   may change them or say why they should differ. A repeat is let through
   and logged as `rule gate released`. It is off by default because it was
   measured against the note and changed nothing: of 7 agents sent back with
   the dependent left behind, all 7 explained a scope choice and stopped
   ([results](../results/rule-gate/README.md)). If an agent keeps leaving a
   file behind, write in the rule's description that the files must agree.
   It reads files, not functions, so it also fires when the task changed a
   part of the file the rule does not touch: on one correct run in six in
   the saved runs.

**Say every way the files are tied, not only the one the proposal found.**
An agent takes the declared rule as the whole contract between the files.
In the experiment that measured this
([results](../results/rule-groups-acted-on/README.md)), agents with
declared rules left a dependent file behind in 4 of 50 runs, against 35 of
50 without. Three of the four losses were on one pair.

- **The proposal:** it paired the manifest's filename function with
  billing's, and the rule said so.
- **The change:** it reordered the manifest's lines.
- **The tie that broke:** billing groups those lines by account, so it
  relies on their order.

The agents checked the change against the declared rule, found the
filename untouched, and left billing alone. A careful description of the
proposed pair would have said the same
([why](../results/rule-groups-described/README.md)). If you know the files
also share an order, a format or a unit, write that in the description too.

Proposals follow the project's source scan, so its `scan.exclude` patterns
leave fixtures, vendored code and generated copies out. Without them, exact
copies in fixture folders head the list. They are real copies, but rarely
the rules you mean to keep in step.

**Limits:**

- Python sources only. Other source files are counted as not examined.
- A proposal is a candidate, not a finding. On the v3 cases, 50 proposals
  per project covered 20 of 51 dependents never used to design the method,
  against 11 for a control and 3.9 at random. On four real projects'
  history it did no better than a control, except where an import already
  joins the two files
  ([results](../results/rule-groups-history/README.md)). Declare the
  rules you know; do not expect the list to find ones you don't.
- An edit to a shared helper that reads no rule input itself is missed.
- Agents act on the brief, on stages chosen for their losses: the
  dependent was left behind in 4 of 50 one-stage runs with every
  breaking pair declared, against 35 of 50 without. With a blind model
  reviewer's choice declared, it was 15 of 50 against 31 of 50.
- On real projects, pairs of protocol methods (`__exit__`, `__repr__`)
  often head the list: 44% of `click`'s top 50 and 84% of `rich`'s.
  Reject them unless the two really keep one rule.
- On a large tree the 30-second default may run out. Reading stops at
  half the budget, so that pairing has the rest, and the list says how
  many Python files were examined; pairs come only from those. Rerun
  with a larger `--seconds` to read them all.

See the [spike and replay](../results/multistage-v3/discover/README.md),
[the acted-on runs](../results/rule-groups-acted-on/README.md),
[the reviewer's rerun](../results/rule-groups-acted-on-reviewed/README.md)
and [real projects](../results/rule-groups-real-projects/README.md).

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
Legacy `delivered` means worker text was available. [Advice delivery observations](advice-delivery.md)
separately identify successful native context flushes and later matching checks;
they do not prove model comprehension or benefit. The 64 KiB writer may evict
older tasks, records that loss, and preserves the active task's attempt allowance.

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

## Ordinary prompt identity

A nonempty first prompt opens a task ID even when it states no coding claim.
Questions and read requests keep their conservative classification. Clearly new
subjects isolate previous task evidence; continuations preserve the original
request and identity. This shared lifecycle applies to every host. Legacy ledgers
with empty IDs receive one at the next prompt without discarding an ongoing claim.
Task existence enables correlation; it does not itself establish verification.

Rehearse prompt-to-edit-to-command correlation without a model with
`python -m eval.advice_delivery NEW_DISPOSABLE_DIRECTORY --ordinary-prompts`.
Replay and synthetic native ingress remain distinct from installed acceptance.
See [current qualification](../docs/validation/2026-10-11-ordinary-session-evidence.md).
