# Declared commands and native invocation capture

ElevenPowers recognizes configured `tests`, `typecheck`, `build`, `lint` and
`benchmark` commands. Recognition records an observed result; it does not launch
the command or infer that an opaque check covered every assertion.

An exact configured command remains supported. The shared runtime also recognizes
one literal directory prefix followed by that exact command:

```sh
cd . && npm run ci
cd "/path/to/project with spaces" && npm run ci
cd "E:/work/project with spaces" && npm run ci
```

The directory must exist and resolve to the project root. Relative paths are
resolved against that root. Supplied tool-directory metadata must also resolve
to the root; conflicting, unavailable or malformed metadata stays incomplete.
A wrapper returning from an explicitly different tool directory is not qualified
by this subset. Directory resolution is a local observation, not an atomic
filesystem transaction or host authentication.

| Invocation | Declared binding |
|---|---|
| Exact configured command | Existing supported case |
| One literal `cd PROJECT && EXACT_COMMAND` | Supported when directory identity qualifies |
| Literal directory is missing or different | Known attempted check retained as incomplete |
| Extra arguments, aliases, pipelines or trailing commands | No automatic equivalence |
| Variables, substitutions, globbing, environment setup, multiple `cd` operations | No automatic equivalence |
| `cd /d`, `Set-Location`, `pushd`, subshell setup | Outside the portable subset |

Double quotes support spaces, but the automatic directory grammar rejects shell
metacharacters and expansion syntax even inside quotes. Use quoted forward-slash
paths for the portable subset. Single quotes, UNC paths, drive-relative forms
such as `C:` and `C:.`, Windows paths rooted without a drive, and any `..` path
component are excluded because shells can resolve them differently. This does
not normalize arbitrary shell programs.
A project can explicitly declare its complete aggregate command; that preserves
the project's existing authority and does not prove the script avoids masking
failures. Known-runner recognition remains a separate heuristic.

## What gets retained

`command` retains the scrubbed observed invocation. `declared_command` retains
the exact configured check. Freshness, milestone history and verification reuse
use the qualified identity while the invocation remains available as provenance.
Legacy receipts without qualified identity continue to use their original command.
The JSON evidence report exposes both fields.

Passing, failing and incomplete attempts remain distinct. Recognized failure
counts override a zero exit. Interrupted execution, running sessions without a
final status, unavailable results and directory attribution gaps cannot provide
a completed passing receipt. A later failed or incomplete attempt replaces the
earlier success for that check, including across task changes. A changed command
declaration still stales its prior receipts; targeted checks retain their scope.

## Reproduce the process controls

With Python and optional Node/npm and Bash installed, select a **new disposable
directory** outside repository boundaries:

```sh
python -m eval.command_invocations NEW_DISPOSABLE_DIRECTORY
```

This writes authored Python/JavaScript projects, runs actual local checks and
feeds their observed results to explicitly marked replay callbacks. It includes
failure, wrong-directory success, interruption and masked-failure controls.
Missing producers are reported as unavailable; they are not installed for you.
An existing destination is refused. These replay controls write no native
activation history and launch no model.

See [observations](../results/native-command-recognition/README.md) and
[validation](../docs/validation/2026-10-08-native-command-recognition.md).
The [earlier installed comparison](../results/behavior-preservation/README.md)
retains its original missing native links. This implementation does not
retroactively qualify that experiment or establish advice consumption, fresh
installed-session acceptance or improved coding outcomes.
