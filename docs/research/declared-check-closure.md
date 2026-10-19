# Declared-check closure: what is borrowed

Every component starts from code already in this repository (Apache-2.0); no
dependency is added.

| Component | Borrowed from | What is added |
|---|---|---|
| Completion annex | exact-declaration matching and `Evidence.freshness` used by milestones and `ep_check.py` | one read-only row per configured declaration, independent of the task verdict |
| Delivery observer | `core/milestones/delivery.py` (prepare → flush → bounded note; documented context fields only) | the same stages for declared-check feedback, plus a malformed-note guard |
| Follow-up join | `core/hosts/readiness.py` receipt links (task/session/time, bounded at 64) | requires the receipt itself to postdate the emission |
| Owned-run link | the random `attempt` digest `core/checks.py` already binds to owned receipts | printing it, and linking only receipts carrying a printed attempt |
| No-model producer | `eval/advice_delivery.py` launcher payloads and the acceptance Node fixture | stage-by-stage declared states and delivery stages over five hosts × two languages × replay/native |

The one-sentence addition: the completion report now shows exact declared-check
state beside the verdict, and the runtime can say whether its feedback reached a
host and whether an exact receipt followed, without claiming the model read it.

The prior diagnosis is [workflow-checks](workflow-checks.md): JavaScript filtered
`node --test` through `tail`, produced generic evidence, and left exact
milestones stale. That result motivated this work and is not reinterpreted.
