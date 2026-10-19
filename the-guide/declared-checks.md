# Reliable declared-check execution

Run one of the project's effective declared properties through ElevenPowers:

```sh
python plugin/bin/ep_check.py --list --project PATH
python plugin/bin/ep_check.py tests --project PATH
python plugin/bin/ep_check.py build --project PATH --seconds 120 --json
python plugin/bin/ep_check.py --all --project PATH --seconds 120 --json
```

The selectors are `tests`, `build`, `typecheck`, `lint` and `benchmark`, when
configured explicitly or discovered from a supported root manifest. Selection
executes the exact configured command in that project directory. It does not
accept arbitrary command text or infer equivalence from shell syntax. Each
explicit invocation runs again; it does not reuse an earlier pass or remove any
other required check. `--list` creates no project state and runs no command.

Startup and explicit new verification tasks expose an owned batch command and
readable argument list. This also applies when the task makes no edits and
infers no coding claim. Per-property and filtered completion/recheck instructions
remain available; a selected check's advice never broadens to all commands.
Labels identify properties outside encoded shell text. Guidance stays bounded
and names omitted instructions; those properties remain required. Advice itself
runs nothing, and passive `off` stays quiet. Duplicate prompts and ordinary
continuations preserve their existing task and do not repeat the advice.

After a completed ordinary verification call, shared host capture also offers
the owned entry point when the corresponding exact declaration is absent, stale
or incomplete. For example, a filtered `node --test ... | tail -15` can leave
fresh generic task evidence while its exact declared milestone remains stale.
The reminder explains that gap and supplies existing bounded runner guidance.
It does not execute the command, infer shell equivalence or promote generic
evidence to an exact or owned receipt.

The reminder is automatic in speaking profiles and bounded by task, selected
declarations and effective configuration. Repeated callbacks do not repeat it;
up to sixteen distinct signatures are retained per task. Current exact receipts,
including failures, need no reminder. Off, owned outer envelopes, unrelated
commands and unfinished/timeout callbacks remain quiet. Known test runners do
not need a literal `tests` argument to receive it. This is transport emission,
not proof that an installed agent reads or follows the advice. See the
[workflow diagnosis and controls](../results/workflow-checks/README.md).

## Run every declared property with one command

`--all` selects supported effective declarations in tests/build/typecheck/lint/
benchmark order and runs each again under one project lock and deadline. Failed
checks do not suppress later independent checks. Every property retains its own
actual result, source/configuration/producer qualification and selected external
input observations. The human output includes one `Declared check PROPERTY:
STATE` line per result. JSON uses `schema_version: 2`, `selected`, `results`,
aggregate `state`, `issues` and elapsed time; individual results keep schema 1.

A batch is passed only when every selected check passes. Incomplete/unrun results
make the batch incomplete; otherwise any failure makes it failed. Task,
configuration or producer movement refuses subsequent execution and prevents a
passing batch at closure. Selections deferred before an owned check begins have
`attempt: null`. Input inspection can retain an incomplete verification attempt
while refusing the child; `unrun: true` means the child executor was not called.
No child result is fabricated. A launch attempt that times out remains incomplete.
The durable verification journal queues the
whole selection before execution, so interruption retains the denominator.

The default 120 seconds is shared by the entire batch, including inspection;
`--seconds` sets the same finite positive <=600-second limit. Existing bounded
cleanup remains separate. `--all`, a property and `--list` are mutually exclusive.
Empty declarations, off, busy ownership and invalid requests launch nothing.
This command runs all selected checks; it does not reuse a prior result. Ordinary
completion retains its existing obligation-based execution rules and does not
automatically launch batches.

The default cooperative allowance is 120 seconds; `--seconds` accepts finite
positive values up to 600. Existing process containment, output limits and a
separate bounded cleanup allowance apply. Exit codes: **0 passed**, **1 failed**,
**2 incomplete/refused**, **130 keyboard interruption**. `off` remains passive
and refuses execution. Busy ownership, missing declarations and unavailable
required inputs also refuse launch.

An incomplete receipt is saved before launch. The owned runner then records the
child's actual exit status and the normal parser evidence. A successful outer
shell trailer cannot replace that receipt with a pass. This does not decode an
arbitrary shell command or establish what an unobserved command did. Reports
contain metadata and redacted declared identities, not captured output.
Generic callback parsing withholds evidence for literal runner envelopes and the
bounded encoded Windows guidance form, so words such as `typecheck` or `benchmark`
in the outer invocation cannot manufacture a later generic pass. Renamed entry
points and arbitrary third-party wrapper scripts are not recognized as owned
envelopes; execute the shipped entry point advertised at startup.

Fresh source and command-specific selected input observations surround execution.
Task replacement, source movement, changed command configuration, runtime changes
and incomplete final reads prevent a current qualified pass. Optional owned
execution metadata keeps configuration/producer qualification separate from
source-byte freshness and selected external-input association. Older receipts
retain their original rules; local state remains unsigned.

Startup advertises an executable runner invocation through the shared host
runtime. Configured milestone recheck advice can include it, and incomplete
completion guidance offers it. Installation does not run this explicit CLI by
itself; existing guide/strict completion verification continues automatically.
All five hosts share the API, without project-specific paths or commands in the
runtime. Synthetic callback exercises are not installed-session acceptance.

Ordinary dirty working trees and non-Git projects use the existing source scan
contract. [PatchProof](patchproof-verification.md) still separately requires an
eligible committed patch for patch binding. A selected passing check does not
mean all required checks passed, the whole task is complete, or a patch is safe.
Commands are trusted project execution, not a sandbox; witness declarations do
not discover every dependency or cover unobserved services/environment.

## See exact declared checks at completion

The completion report lists every configured supported declaration under its
newest exact receipt: `CURRENT`, `FAILED`, `STALE`, `ABSENT` or `INCOMPLETE`.
Only the configured command for that property counts. A generic passing run,
such as the same runner piped through `tail`, can make the task `VERIFIED` while
its declaration stays `ABSENT` or `STALE`, and the report now shows both. The
section is informational: it does not change the verdict, run a command, add a
blocker or promote a receipt.

When generic verification leaves an exact gap, the existing feedback names the
owned runner. The runtime then records up to three separate facts, stored as
hashes and bounded metadata only:

- **intent** — the feedback was generated;
- **emitted** — a host launcher flushed it in a supported context field
  (`additionalContext` or `additional_context`, top level or under
  `hookSpecificOutput`) while the same installation generation was active;
- **later exact native receipt** — after that emission, the same host session
  returned an exact receipt for the declaration, and that receipt is itself
  newer than the emission.

Replay launchers, other response fields, truncated text, removed, reconfigured
or reinstalled integrations record intent at most. The report labels the whole
section `model consumption unproven`: a later receipt is temporal correlation,
not evidence that a model read or followed the feedback.

Each owned result prints `Attempt: <64 hex>` (JSON already carried `attempt`).
The owned runner's output is still never parsed as evidence. A host callback
for an owned envelope only links the ledger receipts already bound to a printed
attempt, so the recommended path is observable without trusting outer output.
An echoed attempt from before the emission links an old receipt and is not
reported as a follow-up. These owned links are kept apart from native receipt
history: they do not count toward health's command capture or installed
acceptance. Refused or unrun checks print no attempt.

See [design](../docs/design/declared-check-execution.md),
[dated qualification](../docs/validation/2026-10-16-declared-check-execution.md)
and [journey 81](../journey/81-the-check-owns-its-exit.md).
For the later batch and readable/no-edit guidance work, see its
[design](../docs/superpowers/specs/2026-10-17-declared-check-adoption-design.md),
[current qualification](../docs/validation/2026-10-17-check-adoption.md) and
[journey 83](../journey/83-one-entry-point-separate-receipts.md).
