# Matched multi-stage comparison at the qualified runner runtime

Execute the existing [four-stage design](../specs/2026-10-16-installed-multistage-design.md)
after the [two installed successes](../../../results/check-adoption/qualification.json).
The user's request explicitly authorizes this comparison and main delivery;
standing permission covers Claude subscription Sonnet 5.5 at medium effort.

## Frozen protocol

- Reuse the existing controller, cases, requests, references and independent
  oracles. No task-specific shipping runtime changes or easier replacement cases.
- Fresh batch at the exact qualified runtime/harness, outside Git ancestors in
  a new system-temp directory. Rehearsal and protocol preparation launch no model.
- Four persistent subscription conversations, four turns each, Sonnet 5.5 medium.
  Each conversation shares 720 model-process seconds; first turn reserves 180,
  unused allowance carries forward. Maximum 48 model-process minutes total,
  plus bounded cleanup and separately recorded controller/grading time.
- Order: Python queue ordinary, Python queue assisted, JavaScript orders assisted,
  JavaScript orders ordinary. Both arms retain equal inputs, permissions and caps;
  only the project-owned ElevenPowers integration differs. Mutation engines off.
- Preserve every scheduled attempt, timeout, scope failure and missing stage.
  No API fallback, favorable retries, evaluator hints or human repairs between
  stages. Native tools are not an OS closed-book boundary.
- Primary outcomes: lost previously passing behavior, earlier-required failures,
  newly introduced failures, final cumulative correctness and paired differences.
  Delivery/adoption stays separate; missing assisted delivery cannot exclude an
  otherwise comparable adverse result. Two authored cases are not population evidence.

## Execution checklist

### Task 1: Preflight, rehearse and freeze

- [x] Verify clean main, current runtime/harness and completed source qualification;
  inspect current automatic CI for actual failures. Reuse the existing pinned venv.
- [x] Run the positive/reference and intended-fault oracle controls, plus fresh
  four-stage no-model rehearsal and independent sixteen-snapshot reproduction.
- [x] Prepare a fresh live batch, validate equal matched public inputs and seal
  the order, requests, baselines, source/oracle identities and time policy.
- [x] Publish sanitized preparation evidence with zero model calls and push.

### Task 2: Execute the four scheduled arms

- [x] Check subscription authentication/model/version without a model probe;
  run each scheduled slot once using the frozen controller.
- [x] Retain per-stage grades, snapshots, identity/scope/delivery and timing,
  including incomplete outcomes; push each completed arm's sanitized record.

### Task 3: Independently reproduce and review

- [x] Export every scheduled slot with the existing source archiver; independently
  regrade the exported snapshots and retain mismatches/missing stages explicitly.
- [x] Compute paired outcomes and regressions without filtering delivery failures.
- [x] One fresh whole-result review of methods, source identities and claims;
  fix only demonstrated material export/accounting defects, with witnessed controls.

### Task 4: Document and deliver

- [x] Update README/status/plan, guides/research/validation, journey 84 and all five
  architecture views, including the next planned work supported by the findings.
- [ ] Render all five map views, validate relative documentation links/privacy,
  push descriptive parts and verify remote main plus actual published map bytes.

## Execution rulings

This instantiates an approved, implemented experiment; it does not redesign the
cases or add a feature. Fresh rehearsal and unchanged-byte checks supplement the
completed four-cell qualification. A redundant documentation-only CI repeat is
not a new source gate, but any actual new failure must be inspected before live
use. Preserve the earlier local setup failure and all four earlier failed native
trials. The two new native successes establish this producer's prerequisite,
not a coding-quality advantage. Retain private raw streams for audit rather than
deleting them before the outcome and source archive can be independently checked.
