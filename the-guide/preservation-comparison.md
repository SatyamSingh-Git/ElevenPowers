# Comparing behavior preservation across tasks

The explicit development comparison in `eval/preservation.py` studies whether
ElevenPowers helps retain earlier behavior while an agent adds later features.
It is research tooling, never an installation action or automatic model call.
The same shipping milestone and hook implementation applies to any project;
the first comparison corpus contains two authored Python systems.

The subsequent [native command qualification](command-capture.md) fixes the
recorded literal-wrapper gap in the generalized runtime. Its local process/replay
controls do not alter this comparison's original native observations or establish
advice consumption and coding benefit.

## Prepare without a model

From the ElevenPowers checkout, with Python, Git and the project's development
environment available:

```sh
python -m pytest tests/test_preservation_cases.py tests/test_preservation.py -q
python -m eval.preservation --prepare NEW_DISPOSABLE_BATCH
```

Preparation refuses an existing destination. It creates ordinary and assisted
copies of a leased queue and an inventory service, initializes their own Git
boundaries and runs the public core tests and separate baseline oracle. Both
arms receive identical production source, public tests, requests and milestone
declarations. Assisted copies explicitly install the existing Claude hooks and
enable bounded milestone advice in guide mode; strength analysis stays off.
Baseline receipts are controller-produced observations, not native captures.

The sealed protocol records source/configuration hashes, oracle identities,
runtime/harness fingerprints, session UUIDs, order and time allowances. Existing
tests and configuration cannot change; the agent can edit the permitted source
and add `tests/test_*.py`. Project settings must stay intact for stage two.

## Execute only with a specific subscription allowance

Each slot uses Sonnet 5 at medium effort, two requests in one resumed Claude
session and at most 480 seconds of total host execution. Grading and preparation
time are separate. Obtain approval for the number of sessions and total time
before launching; the example commands do not grant it.

```sh
python -m eval.preservation --execute BATCH --slot queue-ordinary --executable PATH_TO_CLAUDE
python -m eval.preservation --execute BATCH --slot queue-assisted --executable PATH_TO_CLAUDE
python -m eval.preservation --execute BATCH --slot inventory-assisted --executable PATH_TO_CLAUDE
python -m eval.preservation --execute BATCH --slot inventory-ordinary --executable PATH_TO_CLAUDE
python -m eval.preservation --summary BATCH
```

Subscription authentication must be observed; API environment overrides are
refused. There is no API fallback or favorable retry. A slot with a result journal
cannot be launched again, even after interruption. Keep the original batch.
Native requests use project/local settings and ordinary host tools; parent
instructions and managed host policy can still apply. Both arms share those
conditions. This is not an OS sandbox or a closed-book evaluation.

## Interpret the result

Stage one adds lease/expiry rules; stage two adds JSON round-trip persistence.
Independent checks examine old behavior and new requirements in fresh private
copies. The grader and gold/fault fixtures are outside candidate directories;
agents receive no private results between stages. Source, test setup errors,
timeouts and incomplete output remain separate from assertion failures.

Every stage archives its request identity, host response, model usage, source
manifest, independent grade, current milestone report and available callback
diagnostics. Native observations require matching session/task identities and
current startup, prompt, edit, command and completion evidence. Replay or an old
callback cannot qualify the current stage. Stored worker delivery metadata alone
does not prove that advice was useful or that a model followed it.

The summary compares each pair's final independent passes and total host time.
An extra fresh receipt is verification evidence; a passing final snapshot is
correctness evidence under the tested contracts. Neither alone establishes a
causal correction. The controller does not archive every pre-intervention
proposal and therefore never claims a linked correction. Ties, failures and
unqualified native sessions must be published alongside any positive observation.

When an evaluator correction is needed, keep original observations and protocol
identities. `eval/preservation_archive.py` regrades saved source only after
checking its exact recorded bytes; it separately qualifies the protocol, allowed
configuration, equal public inputs and time/model allowances before comparing
pairs. An unqualified protocol may retain a useful source grade. See the
[first published comparison](../results/behavior-preservation/README.md) for
original and corrected grades and model-free reproduction.

The corpus and oracle are evaluation fixtures, separate from generalized runtime
logic. Extend the frozen evaluation deliberately with independently specified
contracts; do not special-case named user repositories in the runtime. Broader
source-pinned projects and independently justified negative references remain
separate acceptance work.

See the [protocol](../docs/design/behavior-preservation.md),
[implementation plan](../docs/superpowers/plans/2026-10-08-behavior-preservation.md)
and [milestone setup](milestones.md).
