# Command-scoped input controls

[Pre-review observations](pre-review.json) contain four actual-command cases
completed in 874.594 seconds, with no model calls, on the recorded runtime.
This is an intermediate mechanism measurement, not final delivery qualification.

Each language compares two independent local consumers under complete explicit
command scopes versus broad schema 1 inputs. After the initial verification,
the controller introduces a dependency fault, executes its consumer independently,
then verifies failure and repair. Both arms preserve pass/fail/pass outcomes.
The scoped arm retains five earlier synthetic native checks per command; subtract
that offset when comparing execution counts. They are controller envelopes around
real processes, not installed-host observations.

In both Python and JavaScript, broad verification executes both declared commands
at all three stages (six owned executions). Scoped verification executes both
initially and only the affected command after fault and repair (four owned
executions). The separate fault probe adds one first-command execution to both
counter sequences. Two independent-command reruns are avoided per language; no
required check is removed or its latest applicable result discarded.

Unchanged nested bundles read each selected file twice. The earlier witnessed
regression read each eight times. These are byte-read counts, not total latency,
CPU, complete environment coverage or coding quality. Missing first inputs leave
the second scope bound; broad receipts remain incomplete. Final qualification,
review repairs and installed observations are recorded separately in the dated
validation record when available.
