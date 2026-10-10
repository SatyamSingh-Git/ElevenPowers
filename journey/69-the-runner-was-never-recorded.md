# 69 — The runner was never recorded

P22 had waited a month for a free answer: would our own passing evidence have
passed without the change? The plan was to re-run saved checks on their base
trees. Before writing it, the base trees were simply collected again. Four of
twenty-two worked.

Nothing the agents did explained the other eighteen. attrs needed a package this
interpreter no longer has; click's collection now fails on a deprecation that a
newer pytest promotes to an error, in a file the patch never touched. The
manifests could not say which pytest had judged those runs, because
`environment()` recorded every tool except the one that decides a verdict. Its
own docstring promised enough to ask whether two runs were the same experiment.

So the runner is recorded now, and the measurement carries a forward control: a
check must still pass on the patched tree today before anything it says about
the old tree counts. Fifty-three checks failed that control. Without it, all
fifty-three would have failed on the old tree too, and been scored as evidence
that discriminates.

What survived is more ordinary than the literature's 46%. Eight of forty-eight
agent checks were vacuous, and seven of those came from patches with no test at
all — a suite cannot tell old code from new when nothing new is tested. Where
the patch carried tests, one check in forty-one passed anyway.

The first sweep was itself wrong by half. It globbed `bundles/` and measured 54
of 106 ledgers, because the chunked sweeps save to `bundles-chunk1/`; it was
published, noticed while checking which arms the corpus covered, and corrected
the same day. The shape held; the denominator doubled.

Two smaller lessons came from running rather than reading. The runtime's parser
counts a collection error as a failed test, and stress's collection pattern also
matches fixture errors. Neither is wrong for its own purpose. Both would have
mislabelled this measurement.

See the [results](../results/reverted/README.md) and
[validation](../docs/validation/2026-10-10-reverted-evidence.md).
