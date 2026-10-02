# Fixed-patch review: provenance and interpretation

The component experiment extends the review decision in PLAN Phase B′. An
untouched checkpoint, ordinary review and review with tool observations start
from the same saved production change. Equal review-call budgets help separate
the observations from merely allowing another review. Engine analysis adds
local work outside that budget; a timing comparison must include it.

The first pilot measures behavioral test additions on already-correct upstream
patches. Keeping production and existing tests fixed removes code-generation
differences from this question. It also narrows the claim: useful test additions
are code-quality evidence, but cannot establish production repair, faster code,
general task success or the value of every completion-gate mechanism.

The implementation borrows these existing pieces:

- Upstream BSD-3-Clause Pallets projects and MIT attrs, with pinned source/test changes, supply
  actual public contracts. The delivery archive retains commit identities and
  licenses for frozen source fault fixtures.
- `core.strength` supplies shipping Cosmic Ray 8.7.0 observations, clean private
  trials, budgets and incomplete states. Cosmic Ray is MIT-licensed. Its sample
  covers whole changed files in producer order; a small sample may miss the
  edited function. A focused command can also leave unrelated file behavior
  untested. Neither situation supplies a confirmed defect automatically.
- B7's historical research fault sample supplies a separate fixed grading set.
  The prior blind Sonnet/Opus classifications qualify meaningfulness where they
  agree; they are model judgments, not infallible human ground truth. Unlabeled,
  disputed and trivial observations remain separate from that endpoint.
- `eval.subscription`, `core.process` and the existing bounded JSON/checksum
  reader supply authentication, contained process lifecycle and archive
  integrity checks. There is no new API client or model fallback.

The added piece is an immutable fixed-input comparison that withholds mutation
targets, retains every review slot and grades only eligible new test files from
fresh source copies. `eval/review_checkpoint.py` owns preparation, protected
input checks, qualified function-level briefs and local grading.
`eval/review_pilot.py` owns explicit subscription calls and durable attempts.
`eval/review_archive.py` inspects saved evidence and can explicitly run local
reproduction tests; inspection launches neither tests nor a model.

This pilot tests an experimental consumer of the product's analysis. It does
not exercise installed-host completion hooks, automatically publish review
guidance to users or close native-host acceptance. CLI safe mode removes ordinary
customizations from both review arms. Native Bash/file tools still do not form
an operating-system exposure boundary, even with forbidden answer retrieval and
selected command denials. Archive hashes are unsigned internal consistency
checks, not proof of authorship or authenticity.

Useful positive evidence requires the ordinary suite to remain green, frozen
meaningful faults to become detectable, equivalent controls to stay accepted,
and the additions to assert valid observable contracts. An interrupted or failed
review can still leave inspectable tests, but is not a completed matched pair.
One selected four-case pilot cannot establish a population treatment effect.
Zero or negative incremental benefit is retained, with analysis coverage and
review failures available to explain what should be improved next.
