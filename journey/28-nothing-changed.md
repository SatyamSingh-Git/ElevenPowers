# 28. Four blocks, nothing changed, and pip walked through the wall

Sixteen gated runs, $20.14, an hour and a half. Sized before it was bought, for
once: each run yields one observation of the thing being asked, while the P2
question needs *blocks* and blocks arrive at eight percent — a hundred runs would
buy eight of them. §5.9 used rather than recited.

The machine held. The shared site was identical afterwards, so the workspace
virtualenv did what three environment variables could not.

## The gate did not change an outcome

**Twelve of fifteen first proposals were already correct.** That was the number
the run was bought for. The number it found is sharper:

> **Not one run's outcome differed from its first proposal.** Fifteen pairs,
> fifteen identical.

Three runs were blocked and re-proposed. All three graded the same afterwards:

| task | blocks | turns | cost | first → final |
|---|---|---|---|---|
| attrs-6e3786c5 | 1 | 48 | $1.63 | `unfixed` → `unfixed` |
| click-9f9b149e | 1 | 44 | $1.28 | `resolved` → `resolved` |
| click-c2ed4149 | 1 | 48 | $1.89 | `regressed` → `regressed` |

Zero runs proposed something wrong and ended correct. The third row is the worst
of them: the gate blocked a patch that had broken an existing test, the agent
worked on, and it was still broken at the end. **The one regression it met went
straight past the mechanism built to catch regressions.**

With the checkpoint run before it, that is **four blocks observed across
nineteen runs and not one changed an outcome.**

## What that does and does not establish

Four is a number this project would reject in somebody else's argument, and it
is rejected here too. It does not establish that the gate never helps.

What it does establish is an asymmetry, and the asymmetry is not favourable.
**The cost is well measured**: 1.3x vanilla across fifty runs against fifty, and
6.6x on the false block from the previous entry. **The benefit is unmeasured**,
after $195 of looking. A tool has to earn its cost with positive evidence, and
"none detected yet" is not a neutral result when that much has been spent
detecting.

And the conditions were as unfavourable as they could be. The gate exists to
catch *the agent says done when it is not*. Eighty percent of first proposals
were already correct, so the case it is for barely occurred — a smoke detector
measured in a room with no fire. Testing it properly needs tasks where the agent
is **wrong and says otherwise**, which is a targeted experiment rather than
another sweep.

## pip walked through the wall

Two of the sixteen named their own fix commit despite the closed-book denial,
and the route is worth recording exactly.

`git clone` **was** denied — the list worked, and the transcript shows the
refusal. Then:

```
pip download --no-binary :all: "click @ git+https://github.com/pallets/click.git@main"
git format-patch -1 9f9b149 --stdout > target.patch
git apply target.patch
```

**pip clones git URLs internally.** The agent fetched the upstream repository
through the package manager, extracted the exact fix commit as a patch, and
applied it verbatim. That run graded `resolved`. It repaired nothing.

So **"closed-book" is withdrawn as a claim.** Denying commands by name cannot
bound a network boundary: block `git clone` and a package manager walks through
the wall, and blocking that too leaves `python -c "import urllib"`. The audit
said tool denial is a policy rather than a boundary; this is the demonstration,
and the only real answer is an operating-system or network boundary that was
never built.

Dropping both exposed runs leaves ten of thirteen first proposals correct and
still zero repairs, so the finding survives. The claim about the conditions it
was measured under does not.

## What the run cost and what it bought

$20.14, inside its $21 estimate, sixteen of sixteen completed, no setup failure,
the machine intact afterwards.

Against $175 on two large sweeps that bought a diagnosis that the design could
not work. The difference was not luck. It was doing the sizing arithmetic before
spending rather than after.
