# Behaviour-diff spike: would watching behaviour have caught the 31 losses?

A $0 throwaway spike, 2026-11-01, over the ElevenPowers arm's 31 lost stages
in the v3 full run. It uses only what the agent had: the project and its
public tests as they stood before the stage.

**Question.** 22 of the 31 lost dependents import no file the agent edited,
so no import graph can find them. Would a detector that records behaviour
have found them? It works in two steps:
1. Run the pre-stage public tests against the tree before and after the stage,
   recording every project function's return values.
2. Flag source files whose behaviour changed but which the agent did not edit.

**Reach** ([`reach.py`](reach.py), [`reach.json`](reach.json)). The public
suite executes every lost dependent's file: 85–100% of its lines in most
losses, and at least 22% in all. So the code is visible to a recorder.

**Result** ([`losses.json`](losses.json); [`behaviour_record.py`](behaviour_record.py),
[`behaviour_diff.py`](behaviour_diff.py), [`run_spike.py`](run_spike.py)).

| | losses |
|---|---|
| dependent flagged | **1 of 31** (a parcelpost billing case) |
| dependent's recorded behaviour changed at all | 1 of 31 |
| files flagged per stage, on average | 3.4 |

**Why it fails.** In 30 of 31 losses the dependent's behaviour under the
public tests did not change. Its code and inputs were unchanged, so it
behaved exactly as before. These losses are dependents left behind:
- a convention moved, such as a precision, a row order, a format or a key;
- a second place encoding that convention kept the old one.

In gradebook stage 4, every report moved to two decimals and flagged; the
export, the dependent, kept `.1f` and did not. The error only shows when the
part that changed is compared with the part that did not, and that needs a
specification of what belongs together.

**What it means.** v3's quiet dependents were built so that mechanical search
fails: they name nothing that changed, and the public suite stays green. By
construction, then, no mechanical detector of changed names or changed
behaviour finds them. They test whether the agent asks "what else encodes
this convention?". So ElevenPowers' lever on these cases is changing what the
agent does, not computing a fact. Its four delivered briefs were not acted on.

A behaviour-diff detector is therefore **not built** on this evidence. The
spike's false-alarm rate on clean stages was not measured; at 1 in 31 it
cannot change the decision.
