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
| **Staleness** | shipped, but coarse — any source edit stales everything | narrowed to each test's import closure, once measurement shows the coarse version is too pessimistic |
| **The completion gate** | shipped — four states, risk-scaled obligations, `cannot_complete` as a real outcome | demoted from the point of the project to one component of a larger system |
| **Flaky-bug tooling** | shipped — a repeat runner with a derived run count. Nothing else in the field has one | instrumentation helpers and a hypothesis ledger |
| **Self-diagnosis** | shipped — `ep-doctor` tests the seam against the real host contract | continuous, as the host changes |
| **Reproducible measurement** | shipped — pinned corpus, pinned model, a score with an interval, run bundles that can be re-graded | the instrument is built; now it has to be pointed at the actual hypothesis |
| **Candidate generation** | not built | Phase C–D: pools of candidate patches, selection without peeking at hidden outcomes |
| **Does any of this make agents better?** | **unanswered** | Phase C–D. This is the question, and it is still open |

---

## The honest summary

**What is genuinely solid.** The evidence layer works and is now well tested — 486 tests, and all twenty defects an external audit reproduced are fixed rather than argued with. The runtime agrees with the host about which commands failed on 174 of 174 real failures across 36,034 commands. The measurement instrument is reproducible: a pinned corpus across five repositories, a pinned model, a score with an interval, and run bundles complete enough for someone who was not there to re-grade them.

**What is genuinely useful today.** The repeat runner, which stands alone and which nothing else ships. Automatic evidence capture, which costs nothing because it reads work you were doing anyway. And the fact that editing a file invalidates the tests that covered it, which is the idea at the centre of this and the reason `make` is the closest analogue.

**What has not been shown.** Whether work produced with the gate on is better than work produced without it. Twelve real bugs said the gate changed nothing on its own at 1.4× the cost. That result stands, and it is why the plan changed: the evidence layer is now understood as something valuable *inside* a stronger search-and-selection system rather than as an independent oracle. Phases C and D are where that gets tested.

**What was withdrawn.** Several published claims, including a 252-run figure that came from dividing required pairs by the wrong rate, and three claims from a ninety-run sweep after an unrelated agent contaminated the machine mid-measurement. Withdrawals are listed in [`PLAN.md`](../PLAN.md) §10 rather than quietly deleted.

If you want the version with every wrong turn included, that is [`journey/`](../journey/) — twenty-four chapters, plus a file of every mistake made.
