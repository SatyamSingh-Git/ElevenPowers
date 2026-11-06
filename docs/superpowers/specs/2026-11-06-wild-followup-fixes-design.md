# In the wild: do agent PRs without a test draw more follow-up fixes?

*Written 2026-11-06, before any file list was fetched or any association looked at.
Only event counts had been read. $0, no model.*

## Why

**ElevenPowers' one measured effect** came from the held-out sweep: among resolved
patches, those no test could tell from their absence fell from 84% to 37%. Almost
all of that came from adding a test:
- 106 of the 107 vacuous patches contained no test file;
- 69 of the 70 non-vacuous ones did.

**The research synthesis** ([audit_2026_11_05](../../research/audit_2026_11_05/README.md))
put a cheap test first: does this matter outside our corpus? If merged agent PRs
that change code without touching a test draw verified follow-up fixes no more
often than those that do, two things lose their premise:
- the reviewer path;
- a CI check sold on it.

## Data

| Source | What it gives | Licence |
|---|---|---|
| ["Who Finishes the Job?"](https://arxiv.org/abs/2609.26847) replication package, `data/digests/rq1_survival_frame.csv` | 4,396 merged agent PRs from AIDev-pop. `ver_event` marks a verified follow-up fix within 30 days: 188 of them. | MIT |
| [AIDev](https://huggingface.co/datasets/hao-li/AIDev) `pull_request.parquet` | Repository and number for each PR. 4,153 of the 4,396 are present. | CC-BY-4.0 |
| GitHub REST `pulls/{n}/files` | Changed paths, with additions and deletions. Fetched once and stored. | — |

The follow-up-fix labels are the authors':
- an LLM judge reached Cohen's κ 0.78 against two human annotators;
- direct-fix precision was 90%.

They are used as published, not re-judged.

**Drops are counted, never silent:**
- PRs missing from the PR table: 243;
- PRs whose file list cannot be fetched (deleted repository, or the API refused);
- PRs whose file list is truncated by the API's cap of 3,000 files.

## Fixed in advance

**Population:** merged agent PRs that change at least one non-test source file.

**Definitions:**
- A source file is one with an extension in `core/evidence.SOURCE_SUFFIXES`.
- A test file is one matching `core/surface.TEST_NAME`. That is the runtime's own
  rule, used unchanged.
- PRs changing only docs, configuration or tests are excluded.

**Exposure:** *no test*. The PR changes source and touches no file matching
`TEST_NAME`.

**Outcome:** `ver_event = 1`.

**Primary analysis:** the Mantel–Haenszel odds ratio of a follow-up fix for *no
test* against *test*, stratified by repository, with a 95% CI. The stratification
compares PRs within the same repository, so a repository's habits cannot pass for
the effect. Repositories with only one exposure level contribute nothing, and how
many PRs that leaves is reported.

**Secondary analyses:**
1. **Pooled, without stratification:** a 2×2 table and Fisher's exact test.
2. **Stratified by agent:** Mantel–Haenszel.
3. **Size.** Logistic regression of the outcome on *no test*, plus log(1 + changed
   source lines) and the agent. Size is the confound that matters: PRs with tests
   are larger (Haque et al., 2601.03556), and larger changes plausibly draw more
   fixes. This biases *against* the hypothesis, so a positive primary result
   survives it. A null primary result has to be read alongside it.

**Smallest effect of interest:** an odds ratio of 1.5.

**What each result means:**

| Primary result | Reading |
|---|---|
| 95% CI entirely above 1 | Supports the premise. Go on to the dynamic stage below on a sample. |
| CI includes 1, upper bound below 1.5 | No support at the smallest effect of interest. The reviewer path and the CI product lose their basis, as the synthesis said. |
| CI covers both 1 and 1.5 | Inconclusive, because the sample is too small for the question. Say so, and do not build on it. |
| CI entirely below 1 | PRs with tests draw *more* fixes. Report it; this is the outcome the size confound predicts. |

**Directions, per PLAN §5.0:**
- **Forward:** the analysis must be able to show an association that exists. A
  synthetic check (a planted association in shuffled labels) is run first and has
  to come out positive.
- **Adversarial:** the same pipeline with the labels permuted within repositories
  must come out null. A permutation null over 1,000 shuffles is reported beside the
  primary result.

## What this does not measure

- **A test file is not a discriminating test.** "Touches a test" is the proxy that
  held on our own corpus (106/107 and 69/70). In the wild, 80.2% of agent test
  patches carry weak oracles (Banik et al.). This is therefore an upper bound on
  how much "has a test" can separate PRs. The dynamic check (run the PR's tests on
  its base and head) is the second stage, and it happens only if this stage
  supports the premise.
- **Follow-up fixes found within 30 days only.** By the authors' own account,
  their linker can miss fixes, so rates are floors.
- **Some test layouts are missed.** `TEST_NAME` does not recognise C#'s
  `Foo.Tests/` projects or Java `FooTest.java` outside a `test/` directory, so
  those PRs count as having no test. The count of affected PRs (C# and Java files
  outside `test/`) is reported.
- **AIDev-pop only:** repositories with more than 100 stars, and agents active
  before August 2025.

## Where it lives

`results/wild-followup/`:
- `fetch.py`: file lists, cached to `files.jsonl`;
- `analyse.py`;
- `README.md`: the result, written after the analysis runs.
