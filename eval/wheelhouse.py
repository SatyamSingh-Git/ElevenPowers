"""A local shelf of build tools, so the registry can be switched off.

    python -m eval.wheelhouse --build      # once, online
    python -m eval.wheelhouse              # what is staged, and is it usable

**The door this closes.** Every repository in the corpus has a released version
on PyPI that already contains its fix. `eval/canary.py` found three of the four
exposures surviving the tool-denial list doing exactly that: a downloaded
`attrs-24.2.0` tree, a `click-8.5.0` wheel, an installed `clickcheck/` tree.
The registry is an answer key, and **every published boundary design allowlists
a registry**, because dependencies need one. `PIP_NO_INDEX=1` shuts it.

**Why that could not simply be set.** Measured on 2026-09-16: with the index
off, an honest `pip install -e .` dies fetching `setuptools` into pip's
*isolated* build environment. Nothing an environment can set turns that
isolation off — `PIP_NO_BUILD_ISOLATION`, `PIP_BUILD_ISOLATION=false|0|no` and
a `pip.ini` with `no-build-isolation = true` were each tried and each ignored,
while the `--no-build-isolation` flag works. `eval.live._sandboxed` returns an
environment; it does not get to add flags to commands the agent types.

So the answer is not to defeat build isolation but to **feed it locally**:
`PIP_FIND_LINKS` pointing at a directory holding the build backends, which pip
reads even with the index off. The isolated environment resolves from the shelf,
the install works, and `pip download click` still has nowhere to go.

**What is staged.** The backends this corpus actually declares, read from the
repositories rather than guessed: `hatchling`, `hatch-vcs`,
`hatch-fancy-pypi-readme` (attrs), `flit_core` (click, jinja2, itsdangerous),
`setuptools` and `wheel` (markupsafe, and the general case).

**It fails safe by refusing to engage.** If the shelf is missing or incomplete,
`live.py` leaves the index alone rather than breaking every install. A guard
that breaks honest work is the guard an agent turns off, and one of the three
before it was observed being turned off mid-run. The cost of that choice is
that the boundary is *opt-in and checkable*, never silently assumed — which is
why `ready()` exists and why the harness prints what it found.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SHELF = HERE / ".wheelhouse"

# Read from the corpus `pyproject.toml` files, not chosen. A backend missing
# here means one repository's install breaks and the rest are unaffected, which
# `ready()` reports rather than discovering during a paid run.
BACKENDS = (
    "setuptools", "wheel",
    "hatchling", "hatch-vcs", "hatch-fancy-pypi-readme",
    "flit_core",
)


def staged(shelf: Path = SHELF) -> set[str]:
    """Distribution names already on the shelf, normalised the way pip does."""
    if not shelf.is_dir():
        return set()
    found = set()
    for path in shelf.iterdir():
        if path.suffix in (".whl", ".gz", ".zip"):
            found.add(path.name.split("-")[0].replace("_", "-").lower())
    return found


def missing(shelf: Path = SHELF) -> list[str]:
    have = staged(shelf)
    return [b for b in BACKENDS if b.replace("_", "-").lower() not in have]


def ready(shelf: Path = SHELF) -> bool:
    """Can the index be switched off without breaking an honest install?"""
    return shelf.is_dir() and not missing(shelf)


def build(shelf: Path = SHELF) -> int:
    """Fetch the backends once, while online. Everything after this is offline."""
    shelf.mkdir(parents=True, exist_ok=True)
    # `--only-binary :all:` would be wrong: `flit_core` publishes wheels but some
    # backends only ship sdists for some versions, and an sdist on the shelf is
    # still resolvable. Let pip pick.
    done = subprocess.run(
        [sys.executable, "-m", "pip", "download", *BACKENDS, "-d", str(shelf)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900,
    )
    if done.returncode != 0:
        print(done.stdout[-600:] or done.stderr[-600:])
        print(f"\ncould not stage the shelf at {shelf}")
        return 1
    return report(shelf)


def report(shelf: Path = SHELF) -> int:
    absent = missing(shelf)
    count = len(list(shelf.glob("*"))) if shelf.is_dir() else 0
    print(f"shelf     {shelf}")
    print(f"files     {count}")
    print(f"backends  {len(BACKENDS) - len(absent)} of {len(BACKENDS)} staged")
    if absent:
        print(f"missing   {', '.join(absent)}")
        print("\nThe index stays ON. `python -m eval.wheelhouse --build` needs network once.")
        return 1
    print("\nReady: eval.live will set PIP_NO_INDEX and point pip at this shelf,")
    print("so a run cannot fetch the released version that already carries its fix.")
    return 0


def main(argv: list[str]) -> int:
    return build() if "--build" in argv else report()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
