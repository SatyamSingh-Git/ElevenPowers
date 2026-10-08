# Observe advice delivery and later checks

Milestone advice is optional, bounded context after a saved edit. Enable it in
the project's configuration only when wanted; installation does not start model
sessions or enable this optional feature. See [milestones](milestones.md).

```json
{
  "profile": "guide",
  "milestone_advice": {"enabled": true}
}
```

The project also needs `elevenpowers.milestones.json`. Once enabled and the host
hooks are active, advice generation and emission tracking happen automatically
within the existing cooldown, worker and per-task limits. They execute no check.

Inspect the result without starting a host, test or engine:

```sh
python plugin/bin/ep_ready.py HOST --project PATH --json
```

`milestone_advice` is separate from required pipeline stages and completion gates.

| State | What was observed |
|---|---|
| `unconfigured` | No milestone declaration is available |
| `disabled` | Advice is disabled or the profile is off |
| `waiting` | No current-task attempt is retained |
| `generated` | The worker returned context; native emission is unobserved |
| `emitted` | A native launcher flushed the prepared advice in a supported context field, correlated to current startup/wiring/runtime |
| `incomplete` | The latest attempt or its diagnostic qualification is unavailable, changed or incomplete |

The historical advice-state value `status=delivered` means the worker returned
text. It does not independently establish native emission. Existing records
remain readable, and no old record is retrospectively qualified.

After emission, the view joins exact recommendation identities to later native
receipt keys in the same task and startup session. A check can be `current`,
`failed`, `stale`, `incomplete` or `unobserved`. Controller-produced receipts,
older checks and another session's activity do not establish that follow-up.
Supported literal directory wrappers retain their configured identity; see
[command capture](command-capture.md).
Only complete command identities surviving context truncation and redaction
qualify; previews and omitted commands do not. Moving or damaged optional state
invalidates this optional view without downgrading required pipeline health.

These are local unsigned observations. Successful output writing does not
authenticate the host or prove the model read the advice. A later matching
command does not show that advice caused it or improved the code. The report
keeps `model_consumption=unproven`. Keep all fallback checks and ordinary review.

Only bounded hashes, scope identifiers, times and outcomes persist in the
ignored advice state. Prompts, context bodies, raw task/session identifiers and
command bodies are excluded. State remains atomic and below 64 KiB; older tasks
can be evicted, with a visible counter. Missing history stays unobserved.

## Repeatable installed exercise

Explicitly prepare a **new disposable directory**, recording the installed host
version. Preparation downloads nothing and makes no model call:

```sh
python plugin/bin/ep_doctor.py --prepare-acceptance NEW_DIR --platform HOST --language python --host-version INSTALLED_VERSION --advice
```

JavaScript is also supported when Node is installed. Follow `EXERCISE.md` in a
real installed session, keeping its tests, declarations and wiring unchanged.
Inspect native acceptance with `ep_doctor.py --acceptance DIR --platform HOST`,
and advice with `ep_ready.py HOST --project DIR --json`. A model session consumes
its normal subscription allowance and requires a specific run budget; preparation
does not authorize one. Native matrix captures retain their base fields, so
inspect the advice result separately.

## Rehearse without a model

```sh
python -m eval.advice_delivery NEW_DISPOSABLE_DIRECTORY
```

The exercise uses unrelated disposable Python and JavaScript fixtures, real
passing/failing checks and real bounded interruption. Each host runs both replay
and **synthetic native-ingress controls**. The latter deliberately call the
launcher as a host would; they are not installed agent sessions. Replays cannot
write qualified native emission or follow-up observations. Results keep those
categories separate and never establish model comprehension or coding benefit.

See [design](../docs/design/advice-delivery-observations.md),
[observations](../results/advice-delivery/README.md) and
[validation](../docs/validation/2026-10-08-advice-delivery-observations.md).
