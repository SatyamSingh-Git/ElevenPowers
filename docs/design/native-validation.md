# Versioned native validation, performance and outcome pilot

Approved direction: close installed-host readiness using the existing disposable
exercises; measure representative costs; evaluate challenging work using the
user's subscription-authenticated Codex and Claude Code CLIs. All runtime behavior
is project-independent. A pilot can return a neutral or negative result. The user
clarified that task size is not the criterion: measure actual coding improvement
through any engaged mechanism, including gates, staleness, blast radius or scope.

## Compatibility evidence

Reuse `core.hosts.acceptance`; do not create a second acceptance engine. Bind
new exercises and actual SessionStart observations to a bounded SHA-256 identity
of shipped runtime files. A later software change invalidates that identity.
Observe installed versions only through explicit, contained `--version` probes.
Operator versions, executable lookup and local hooks remain unsigned metadata.

An explicit capture reads one current acceptance result and writes no project
state. It exports whitelisted outcomes, checks, version, software identity and
time, without project paths, prompts, source or tool output. A matrix includes
all five hosts and both exercise languages; missing entries remain waiting.
Saved results are dated observations, never a fresh certification of a project.
Malformed, conflicting, unbound or mismatched evidence cannot become passed.

## Performance

Explicit repeated health reads reuse the existing read-only inspector. Default
three reads, maximum twenty, total cooperative budget sixty seconds and maximum
one hundred twenty seconds. Every attempted read is retained, including failed
or incomplete coverage; do not discard slow reads. Record warmup policy, sample
count, source size, Python/OS, software identity and completion of the sample.
Separate current scan/report/read timings from retained callback samples and
automatic command times. Handler samples exclude host launch/final registry
write; Stop may include verification and is not pure plugin overhead.
Median/p95 describe only the retained sample, not universal latency or a speedup.

## Coding-outcome pilot

Use a frozen multi-module behavioral task and an evaluator outside each agent
workspace. Keep visible tests and issue identical across baseline and tool arms;
freeze evaluator, source and prompt fingerprints before model runs. Reuse the
existing process containment, Git and evaluator patterns. New runner supports
explicit subscription CLIs only, refuses API-key environment overrides, has no
API fallback, and never runs from plugin installation or completion hooks.

Use exactly `gpt-6.1-sol` at medium for Codex and `claude-sonnet-5-5` at medium
for Claude. Do not silently substitute an unavailable model or use API billing.
Limit the first pilot to Codex and Claude Code, baseline/tool arms and two
replicates per arm, at most eight model runs and four minutes per run. Both arms
use the same model, effort, tools and wall-clock allowance. Rotate arm order.
Keep setup errors, timeouts and failed evaluation separate from unresolved tasks.
Grade the exported candidate independently; unchanged grader/visible contracts
and coverage are prerequisites. Preserve every bounded run record immediately.
Local filesystem separation is not a closed-book OS boundary; report this limit.

Record hidden behavioral successes, regressions, false-completion outcomes,
mechanisms actually engaged, completion time and available usage. Improvements
in evidence quality and patch behavior are separate outcomes. A task solved by
every baseline provides no evidence of increased solve rate.
Do not change the task, graders or sample count after seeing arm results. Eight
runs are a descriptive pilot, not proof of general benefit or statistical power.
Installation/trust/policy and unavailable host logins remain explicit gaps.

## Delivery

Nineteen meaningful incremental pushes, descriptive messages without counters.
Inline execution with one fresh final review; regression tests observed failing
then passing for behavior changes. Focused checks during implementation and full
suite/audit/grader/architecture at the delivery boundary. Update all six guides,
README (feature section, not opening), plan/status/roadmap, journey and validation.
Publish the verified result on main, preserving existing user work and history.
