# Reliable declared-check execution

Run one of the project's effective declared properties through ElevenPowers:

```sh
python plugin/bin/ep_check.py --list --project PATH
python plugin/bin/ep_check.py tests --project PATH
python plugin/bin/ep_check.py build --project PATH --seconds 120 --json
```

The selectors are `tests`, `build`, `typecheck`, `lint` and `benchmark`, when
configured explicitly or discovered from a supported root manifest. Selection
executes the exact configured command in that project directory. It does not
accept arbitrary command text or infer equivalence from shell syntax. Each
explicit invocation runs again; it does not reuse an earlier pass or remove any
other required check. `--list` creates no project state and runs no command.

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

See [design](../docs/design/declared-check-execution.md),
[dated qualification](../docs/validation/2026-10-16-declared-check-execution.md)
and [journey 81](../journey/81-the-check-owns-its-exit.md).
