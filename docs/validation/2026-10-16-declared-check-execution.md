# Reliable Declared-Check Execution v1 — validation

Status: implementation and final qualification in progress; no new model session.

## CI investigation

Main repeat [38623263659](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38623263659)
failed `test_actual_producer_keeps_replay_and_native_ingress_distinct[javascript]`
on Windows 3.13: 1 failed, 2,414 passed, 5 skipped in 2965.32 seconds. The original
assertion retained only `qualified=False`; no failing component summary artifact
exists for that cell. No cause or repair is established by that log.

Twelve subsequent local actual JavaScript exercises qualified. The diagnostic
change exposes the qualification predicates and includes the full result in
pytest failures. Existing producer tests passed 4/4 in 39.33 seconds.
[Diagnostic hosted run 38885046886](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38885046886)
passed all four OS/Python cells: twenty JavaScript exercises per cell, eighty
total, plus retained execution controls configured for thirty repetitions per cell. The original failure
remains unexplained; these are diagnostic coverage and successful repetitions,
not evidence of a repaired root cause.

## Witnessed controls

- Runner controls: 18 failures against the absent API, then 18 passed in 9.33s.
- CLI controls fail before the CLI exists; actual outer-shell masking, real
  child outcomes, read-only listing, invalid requests and private-output
  exclusion passed afterward. Actual CLI termination retains provisional evidence.
- Actual Python/Node integration: both controls passed in 31.18s. Each preserves
  `STALE/CURRENT -> FAILED/CURRENT -> CURRENT/CURRENT`, with launches `[3,1]`
  before missing-input refusal. The outer shell exits zero; all five synthetic
  post callbacks preserve the failed owned receipt.
- Startup executable guidance and guide/strict completion guidance were seen
  missing before implementation. The emitted invocation runs the actual CLI.
- A configuration-only change was initially conflated with source freshness;
  its regression failed before separating the execution association from source
  facts. Final qualification below supersedes intermediate runs.

## Limits and remaining qualification

Full regressions, independent gates, fresh review, final hosted protocol/artifact
checks and rendered architecture are pending. No installed session or model was
launched. Ordinary dirty/non-Git execution and exact committed PatchProof binding
remain distinct. No complete dependency discovery, universal safety, attestation
or causal coding-quality/latency improvement is established.
