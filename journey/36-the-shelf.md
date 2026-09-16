# 36. A shelf, and the registry finally shut

The last open door from [entry 34](34-the-ratchet.md), closed. Small piece of
work, and the reason it took two attempts is the useful part.

## The door

Every repository in the corpus has a released version on PyPI that **already
contains its own fix**. `eval/canary.py` caught three of the four exposures
surviving the tool-denial list doing precisely that:

```
/tmp/attrs_dl/242/attrs-24.2.0/tests/...      downloaded release
/tmp/clickdl  click-8.5.0-py3-none-any.whl    downloaded wheel
Temp\clickcheck\installed\click\...           installed release
```

The registry is an answer key. And **every published boundary design allowlists
a registry**, because dependencies need one — so this door is open in all of
them, not only here. Docker would not have closed it.

## Why `PIP_NO_INDEX` alone failed

It shuts the registry. Measured: `pip download click` blocked, `pip install
click==8.5.0` blocked.

It also killed `pip install -e .`, because pip builds in an **isolated**
environment and fetches `setuptools` into *that* from the index.

Turning the isolation off cannot be done from where `_sandboxed` stands. All
measured, all ignored:

| | |
|---|---|
| `PIP_NO_BUILD_ISOLATION=1` | ignored |
| `PIP_BUILD_ISOLATION=false` / `0` / `no` | ignored |
| `pip.ini` with `no-build-isolation = true` | ignored |
| `--no-build-isolation` on the command line | **works** |

`_sandboxed` returns an environment. It does not get to add flags to commands
the agent types.

## The shelf

So do not fight the isolation — **feed it**. `PIP_FIND_LINKS` points at a local
directory, and pip reads it *with the index off*. The isolated build resolves
`setuptools` from the shelf; `pip download click` still has nowhere to go.

What is staged was read from the corpus rather than guessed:

```
attrs         hatchling, hatch-vcs, hatch-fancy-pypi-readme
click         flit_core
jinja2        flit_core
itsdangerous  flit_core
markupsafe    setuptools
```

Six backends, thirteen files, fetched once while online. Every run after that is
offline.

## The part that is a design decision, not a detail

**It engages only when the shelf is complete.** An incomplete shelf plus a
closed index breaks every install — which is `PIP_USER`, `PYTHONUSERBASE` and
`PIP_REQUIRE_VIRTUALENV` all over again, and one of those three was *observed
being switched off by an agent mid-run*.

So the boundary is **opt-in and checkable** rather than silently assumed:

```
$ python -m eval.wheelhouse
shelf     E:\ElevenPowers\.wheelhouse
files     13
backends  6 of 6 staged
```

The cost of that choice is honest: a missing shelf means the door is open, and
nothing pretends otherwise. `eval.canary` remains the thing that says whether it
actually held.

Three tests, three directions:

- **adversarial** — `pip download click` and `pip install click==8.5.0` both fail
- **forward** — `pip install -e .` succeeds offline, and the result imports
- **fail-safe** — with no shelf, `PIP_NO_INDEX` is *absent* from the environment

The third is the one that would have caught the first attempt. Against real pip
throughout: a mocked pip would test the mock, and the whole question is what pip
does with an isolated build environment.

561 tests.

## Where the boundary now stands

| Channel | State |
|---|---|
| git history | **closed by construction** — `materialise` uses `git archive`, so the workspace never has a `.git` from upstream |
| upstream network | **closed** — denial list, measured **14 → 0** between the pre- and post-denial sweeps |
| package registry | **closed** — this entry |
| the machine's own `site-packages` | **open, and detected** |

That last row is not a boundary and is not claimed as one. The workspace venv
uses `--system-site-packages` — entry 27's fix, the one that finally stopped
agents installing into the machine — so the installed copy of the library under
test is readable by absolute path, and it is a newer release carrying the fix.
Preventing a *read* needs containment, which this machine does not have. The
canary measures it: one run of the sixteen in the post-denial sweep.

So: three of four doors shut, the fourth measured rather than assumed. That is
the most the plan's §4.1 can honestly claim without a container, and it is
enough that a sweep now means something it did not mean last week.
