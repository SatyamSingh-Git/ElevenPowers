# 89 — the gap held on code nobody here picked

Journey 88 ended with 40 tasks that rehearsed clean and a harness that had not
yet spent anything. B9 had found fewer VACUOUS patches under the gate, 8% against
22%, on a corpus this project chose; `PLAN.md` §10 said only vacuity by arm, on
tasks sourced by a rule fixed first, would settle whether that was ElevenPowers or
the corpus.

## A pilot that qualified the harness

Eight runs, four tasks from four repositories, one per arm: every run completed on
the exact model, every assisted run fired hooks and kept a ledger, no ordinary run
did, and the analysis read the collected records end to end. $0.46. The first run
was the shape the question is about: the ordinary agent searched, edited two lines
and stopped, with no test run and none added, and the probe called it VACUOUS.

## 240 runs, sealed and never retried

The schedule was pushed before the first launch. Ordinary resolved patches were
VACUOUS in 74 of 88 runs, 84%; assisted, installed at the default `guide` profile,
in 33 of 89, 37%. Per task, ElevenPowers was lower on 17 and higher on 1, with 13
tied and 9 dropped because an arm resolved nothing: signed-rank p = 0.00016.
Resolve rates did not move. Assisted runs took about three times the model time.

And it is, again, whether a test is written at all. 106 of the 107 VACUOUS
patches contained no test file; 69 of the 70 that were not did. Ordinary agents
added a test in 14 of 88 resolved runs, assisted agents in 56 of 89.

## What went wrong on the way

- **The session ended with the sweep at 233 of 240.** The slot in flight was left
  as launched and, under the never-retry rule, stays incomplete; the six never
  started were run afterwards as first attempts.
- **The quota guard stopped the resumed run before it launched anything.** It read
  the whole log, counted the killed driver's last lines as fresh host failures,
  and did what it was written to do. It now reads only lines after the latest
  resume marker. Nothing was consumed.
- **The analysis was run once on the incomplete record** while that stop was being
  understood. Nothing was changed in response; the result above is the analysis
  of all 240.
- **One assisted run was excluded as a closed-book breach** for `pip install -e .`,
  a local editable install. The frozen rule treats any `pip install` as a reach,
  so the run, resolved and not VACUOUS, does not count. Excluding it works against
  the assisted arm, as does the run cut off by the session and one ordinary run
  whose probe went unscored.

## What it does not show

One model, at medium effort, through one host, on Python fixes with a median of
ten changed lines, from twelve repositories whose frame excludes build-generated
modules, suites that read their own metadata, test dependencies outside the
install order, and subtest-only rejections. VACUOUS says the repository's own
tests cannot tell the patch from its absence; it does not say the patch is wrong.
