# What's Offered

What ElevenPowers does today, what is coming, and an honest account of where it stands against everything else.

---

| | |
|---|---|
| **[features.md](features.md)** | every capability that exists right now, with its evidence and its limits |
| **[roadmap.md](roadmap.md)** | the five phases, what each one has to prove, and what is deliberately not built |
| **[how-it-compares.md](how-it-compares.md)** | against the fourteen systems read from source — where this is genuinely ahead, where it is behind, and what it would take to lead |

---

## In one table

| | Today | Where it is going |
|---|---|---|
| **Evidence capture** | shipped — reads the commands your agent already runs, no protocol, no cooperation required | unchanged; this is the foundation everything else sits on |
| **Automatic setup** | shipped — startup health, manifest command discovery and coverage reporting | installed Snag session and full CI validation |
| **Project health** | shipped — one fresh staged view, aggregate command outcomes, native delivery and bounded timings | representative ordinary-session measurements; no speed claim yet |
| **Native acceptance** | shipped — explicit disposable Python/Node exercises and read-only contract qualification for five hosts | versioned installed sessions, separate from the ten passing producer/launcher controls |
| **Host integrations** | Claude Code plus native Codex, Gemini CLI, Cursor Agent and Copilot CLI adapters, setup, diagnostics and bundles | versioned live-session acceptance for the four additions; [capabilities and limits](../the-guide/platforms.md) |
| **Repository selection** | shipped — Git ignores, project boundaries, budgets and explicit scan gaps | measure real-project latency and coverage |
| **Staleness** | shipped, but coarse — changes within selected source inputs stale evidence | narrowed to each test's import closure, once measurement shows the coarse version is too pessimistic |
| **Milestone behavior evidence** | shipped — optional project declarations, automatic cross-task receipt retention and fresh separate status/export | qualify precise native attribution, normal usage cost and end-to-end benefit; [scope and limits](../the-guide/milestones.md) |
| **The completion gate** | shipped — four states, risk-scaled obligations, `cannot_complete` as a real outcome | demoted from the point of the project to one component of a larger system |
| **Flaky-bug tooling** | shipped — a repeat runner with a derived run count. Nothing else in the field has one | instrumentation helpers and a hypothesis ledger |
| **Self-diagnosis** | startup health is automatic; `ep-doctor --host` provides a deeper launcher check | continuous, as the host changes |
| **Reproducible measurement** | shipped — pinned corpus, pinned model, a score with an interval, run bundles that can be re-graded | the instrument is built; now it has to be pointed at the actual hypothesis |
| **Changed-region test strength** | shipped — optional real engines, Git hunks/functions, contained spans, file-weighted samples and measured-command reports | held-out behavioral improvement beyond ordinary review; [actual relevance evidence](../docs/validation/2026-10-03-strength-regions.md) |
| **Candidate generation** | not built | Phase C–D: pools of candidate patches, selection without peeking at hidden outcomes |
| **Does any of this make agents better?** | **unanswered** | Phase C–D. This is the question, and it is still open |

---

## The honest summary

**What is genuinely solid.** The evidence layer works and is now well tested, and every defect an external audit reproduced is fixed rather than argued with. The runtime agrees with the host about which commands failed on 174 of 174 real failures across 36,034 commands. The measurement instrument is reproducible: a pinned corpus across five repositories, a pinned model, a score with an interval, and run bundles complete enough for someone who was not there to re-grade them.

**What is genuinely useful today.** The repeat runner, which stands alone and which nothing else ships. Automatic evidence capture, which costs nothing because it reads work you were doing anyway. And the fact that editing a file invalidates the tests that covered it, which is the idea at the centre of this and the reason `make` is the closest analogue.

**What has not been shown.** Whether work produced with the gate on is better than work produced without it. Twelve real bugs said the gate changed nothing on its own at 1.4× the cost. That result stands, and it is why the plan changed: the evidence layer is now understood as something valuable *inside* a stronger search-and-selection system rather than as an independent oracle. Phases C and D are where that gets tested.

**What was withdrawn.** Several published claims, including a 252-run figure that came from dividing required pairs by the wrong rate, and three claims from a ninety-run sweep after an unrelated agent contaminated the machine mid-measurement. Withdrawals are listed in [`PLAN.md`](../PLAN.md) §10 rather than quietly deleted.

If you want the version with every wrong turn included, see the [journey index](../journey/README.md), including [the native platform delivery](../journey/49-one-engine-several-hosts.md), and the record of mistakes and corrections.

Explicit [milestone rechecks](../the-guide/milestones.md#explained-exact-rechecks)
now turn dependency leads into exact declared commands, with evidence states and
fallback verification preserved. [Measured controls](../results/milestone-rechecks/README.md)
include a retained subprocess miss and descriptive added read cost.
