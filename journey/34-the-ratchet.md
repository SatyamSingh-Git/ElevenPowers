# 34. Keeping the best state, and one guard that had to be taken back out

Two things this sitting, and the second is the more useful entry.

## The ratchet

`core/ratchet.py`. PLAN §5.6 has said since v0.7 that *a long attempt ends at
its latest patch, not its best*, and the 2026 literature put a number on it:
**60-69% of coding-agent failures reach and edit the correct functions** and
still produce a wrong patch, with five documented cases producing the reference
solution mid-trajectory and then corrupting it.

When the declared checks are green at a stop, the working tree is committed to a
private ref under `refs/elevenpowers/proven`. If the tree later moves off it, the
end report says so and prints the diff and restore commands.

**Borrowed, per [build-on.md](../docs/research/build-on.md).** The store is
**Cline's** — snapshots in private refs, nothing of the user's touched — and so
is the **compare-and-swap refusal when HEAD has moved**. That refusal is the
part worth having: the 2026 recoverability work found checkpoint-only recovery
choosing an *ineligible* source in every eligibility challenge while restoring
bytes perfectly and satisfying every final invariant, and concluded that **task
success cannot detect a bad recovery decision**. A paper named the gap; Cline
had already closed it.

**Ours is one sentence: when to snapshot.** Everyone else snapshots per edit,
which is why the published cost of this intervention is *10 to 40 times the test
invocations*. This snapshots only when the ledger already says the declared
checks are green and fresh — a fact `evidence.py` computes on every edit and
then throws away. The expensive part of the idea is the part invalidation makes
free.

Three details that are the difference between a feature and a liability:

- **A temporary index.** `git add -A` against the repository's own index would
  stage the agent's work as a side effect of observing it. A runtime that
  changes what it measures is the defect this project keeps finding elsewhere.
- **Untracked files are included.** The test an agent just wrote is untracked
  and is exactly the thing worth keeping.
- **It offers; it never restores.** Same rule as `stress.py`, same reason
  (§5.12).

Seven tests against a real `git init`, both directions: a proven state is
offered back after the tree moves; nothing is offered when nothing was proven,
when the tree has not moved, or when HEAD has. A module that offered on every
stop would pass the first test alone; one that never offered would pass the
other three.

## The guard that went back out again

The canary had just found what survives the denial list. Every survivor was the
same thing: **a released version of the package that already contains the fix.**

```
/tmp/attrs_dl/242/attrs-24.2.0/tests/...        downloaded release
/tmp/clickdl  click-8.5.0-py3-none-any.whl      downloaded wheel
Temp\clickcheck\installed\click\decorators.py   installed release
site-packages\click\_textwrap.py                the machine's own copy
```

The registry is an answer key. And every published boundary design allowlists a
package registry, because you need one for dependencies — so this door is open
in all of them, not only here.

`PIP_NO_INDEX=1` closes three of the four. Measured adversarially: `pip download
click` blocked, `pip install click==8.5.0` blocked.

Then the forward direction: **`pip install -e .` broke.** pip builds in an
*isolated* environment and fetches `setuptools` into it from the index, so with
the index off an honest install dies.

Turning isolation off cannot be done from where this code stands. Measured, all
ignored:

| | |
|---|---|
| `PIP_NO_BUILD_ISOLATION=1` | ignored |
| `PIP_BUILD_ISOLATION=false` / `0` / `no` | ignored |
| `pip.ini` with `no-build-isolation = true` | ignored |
| `--no-build-isolation` on the command line | **works** |

`_sandboxed` returns an environment. It does not get to add flags to commands
the agent types.

**So it came back out.** Shipping it would have repeated the exact mistake of
the three guards before it — `PIP_USER`, `PYTHONUSERBASE`,
`PIP_REQUIRE_VIRTUALENV` — each of which broke something honest, and one of
which was *observed being switched off by an agent mid-run*. A guard that breaks
real work is a guard that gets turned off, and then there is no guard and a
false sense of one.

The fix is real work rather than an environment variable: a wheelhouse holding
`setuptools` and `wheel`, built once while online, with `PIP_FIND_LINKS`. That
is defined and not done.

**It was the repository's own probe that caught it** —
`test_an_install_stays_in_the_workspace_even_when_the_guard_is_off`, written
after entry 27's install incident. And I nearly missed it: a first run with
`-k agent` did not match that test's name and came back green. The suite is the
authority, not a filter over it.

## What stands

- The denial list works. Upstream network exposure went **14 → 0** between the
  pre-denial and post-denial sweeps, on the same screen. That is the canary seen
  to flip, which §4.1 requires before a boundary may be trusted.
- What survives the denial is the **package registry and the machine's own
  installed copies** — a channel no network allowlist closes, because the
  allowlist has to include the registry.
- `PIP_NO_INDEX` would close most of it and cannot ship until the wheelhouse
  exists.
- Reading the machine's `site-packages` by absolute path is not preventable
  without containment at all. It is detectable, and the canary detects it.

555 tests.
