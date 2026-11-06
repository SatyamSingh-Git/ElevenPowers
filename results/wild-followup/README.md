# In the wild: do agent PRs without a test draw more follow-up fixes?

*Run 2026-11-06, $0, no model. The analysis was fixed in
[the design](../../docs/superpowers/specs/2026-11-06-wild-followup-fixes-design.md),
committed (`1af2de5`) before any file list was fetched.*

## Result: inconclusive, by the rule set in advance

Within repositories, merged agent PRs that change code without touching a test
drew verified follow-up fixes at an **odds ratio of 0.91 (95% CI 0.54–1.54)**
against PRs that touched one. That interval covers both no effect and the
smallest effect of interest (1.5). The design's rule for that case: say so, and
do not build on it.

**This does not show that tests don't matter in the wild.** The study could not
reliably have seen an odds ratio of 1.5: its power there was 39%. It does not
support the premise either, and the comparison it trusted most, within the same
repository, leans the other way.

| | Odds ratio | 95% CI |
|---|---|---|
| **Primary:** Mantel–Haenszel within repository (2,253 PRs in the 165 repositories with both kinds) | **0.91** | 0.54–1.54 |
| Permutation null, labels shuffled within repository (1,000 shuffles) | p = 0.70 | |
| Pooled 2×2 | 5.3% vs 3.9% fixed; Fisher p = 0.16 | |
| Mantel–Haenszel by agent | 1.28 | 0.86–1.90 |
| Logistic regression: no test + log size + agent | 1.46 | 0.98–2.18 |

**The two comparisons point different ways:**
- **Between repositories,** PRs without tests come out worse. The size-adjusted
  estimate (1.46) points the way the premise does.
- **Within a repository,** they don't (0.91).

The design anticipated the size confound. PRs with tests are larger, and larger
changes draw more fixes: 1.37× the odds per unit of log changed lines. Adjusting
for size moved the estimate up, as predicted. The stratified primary also
removes what differs between repositories, such as how actively a project
fixes things at all. The gap between the two readings is what that leaves, so
the honest reading is that *which repository* explains more than *whether this
PR had a test*.

**Both directions of the analysis worked:**
- **Forward:** an association planted at twice the odds was found (1.33–3.42).
- **Adversarial:** shuffled labels came out null.

| Power (200 simulations at the observed base rate) | |
|---|---|
| Odds ratio 1.5 | 0.39 |
| Odds ratio 2.0 | 0.885 |

## Population

| | PRs |
|---|---|
| Merged agent PRs with a follow-up-fix label | 4,396 |
| Not in AIDev's PR table | 243 dropped (none had a fix) |
| File list returned 404 | 13 dropped |
| File list at GitHub's 3,000-file cap | 1 dropped |
| Changed no non-test source file | 980 excluded |
| **Analysed** | **3,159** in 514 repositories |
| No test touched | 2,323, of which 122 (5.3%) were fixed |
| A test touched | 836, of which 33 (3.9%) were fixed |

## What bounds it

- **The proxy is crude.** "Touched a test file" is not "has a test that tells
  the change from its absence". It held on our own corpus: 106 of 107 vacuous
  patches had no test file, and 69 of 70 non-vacuous ones did. In the wild, most
  agent test patches carry weak assertions (80.2% by Banik et al.'s classifier).
- **Fewer than half the PRs were followed for the full 30 days.** 2,220 of the
  4,153 have no fix and a follow-up window shorter than 30 days, so the binary
  outcome undercounts fixes.
  - *Exploratory, not in the design:* the window was cut short slightly more
    often for PRs with a test (58.3% against 52.2%). That gives them less time
    to draw a fix, which favours the premise. A survival analysis would use the
    windows; the design fixed a binary outcome, so this is reported, not
    re-analysed.
- **The fix labels are the authors'.** An LLM judge reached κ 0.78 against two
  human annotators, with 90% direct-fix precision. Their linker can miss fixes.
- **Some test layouts are missed.** `core/surface.TEST_NAME` misses C#'s
  `*.Tests` projects and Java's `*Test.java` outside a `test/` directory. 19
  "no test" PRs have such files.
- **The sample is narrow:** AIDev-pop only, meaning repositories with more than
  100 stars and agents active before August 2025.

## What it means for the plan

The [synthesis](../../docs/research/audit_2026_11_05/README.md) put this test
first because a null here would remove the premise of both the reviewer path
and a CI check sold on test discrimination. It is not a null; it is too small to
tell. The dynamic stage (running each PR's tests on its base and head) was
conditional on support here, so it is not run.

A larger test would need follow-up-fix labels on more of AIDev's 932,791 PRs.
That means re-running the authors' linker and judge, which is a paid model step
and not done here.

## Reproduce

```bash
python build.py <rq1_survival_frame.csv> <AIDev pull_request.parquet>  # needs pyarrow; writes prs.csv
python fetch.py      # gh CLI; resumable; writes files.jsonl
python analyse.py    # standard library; writes summary.json
```

`prs.csv` and `files.jsonl` are committed, so `analyse.py` reruns without
either download.

## Sources

- **Follow-up-fix labels:** Takerngsaksiri, Duong and Barnett, ["Who Finishes
  the Job?"](https://arxiv.org/abs/2609.26847), replication package
  `wannita901/pr-fix-authorship` (MIT).
- **PRs:** [AIDev](https://huggingface.co/datasets/hao-li/AIDev) (Li, Zhang and
  Hassan, arXiv 2602.09185; CC-BY-4.0).
