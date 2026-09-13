"""Mine several repositories into one corpus, and say what is in it.

    python -m eval.corpus --repos DIR --out corpus.json [--want 6] [--limit 200]
    python -m eval.corpus --repos DIR --out corpus.json --only markupsafe,jinja2
    python -m eval.corpus --show corpus.json
    python -m eval.corpus --lock corpus.json --out corpus.lock
    python -m eval.corpus --rebuild corpus.lock --repos DIR --out corpus.json

Every task suite this project has measured itself against came from one place,
and twice that turned out to matter. Hand-written suites agreed with the
assumptions of the code they were grading; the mined suite came from a single
repository, so one project's testing habits decided what a task looked like.
Several repositories is not a large number of repositories, and it is the
difference between a property of the corpus and a property of one codebase.

**The corpus is pinned, not re-discovered.** A built corpus is ~1.8MB of test
bodies and preservation sets, too large to keep in git and too important to
rebuild by chance: scanning "the last 150 commits" of five repositories gives a
different answer every week as those repositories gain commits, so a rerun would
score a different benchmark and call it the same one. `--lock` writes the few
kilobytes that identify it — origin, base and fix commit per instance — and
`--rebuild` reconstructs it from exactly those, refusing rather than
substituting when a commit is missing.

**Difficulty is a label here, never a filter.** The rule this project used
before — keep a task only if the naive fix breaks the visible suite — selected
the benchmark around the mechanism being measured, which is audit finding E6. A
corpus that only contains tasks the gate can win is not evidence about the gate.
So each instance carries the measured size of the maintainer's own source change
and is reported by band; nothing is dropped for being easy or hard, and the
bands exist so a gain concentrated in one of them cannot hide inside an average.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from .mine import Instance, candidates, validate

# Bands over the maintainer's own source change, in lines. Objective and
# computed, rather than a judgement about how hard a task feels.
BANDS = (("one-liner", 1, 3), ("small", 4, 20), ("substantial", 21, 10**9))


def band(lines: int) -> str:
    for name, low, high in BANDS:
        if low <= lines <= high:
            return name
    return "empty"


def mine_repo(repo: Path, want: int, limit: int, env: dict[str, str],
              source_dir: str, test_dir: str) -> list[Instance]:
    found: list[Instance] = []
    rejected: dict[str, int] = {}
    pool = candidates(repo, limit, source_dir, test_dir)
    print(f"  {repo.name}: {len(pool)} commit(s) changed source and tests together")
    for sha, tests in pool:
        if len(found) >= want:
            break
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            try:
                instance, why = validate(repo, sha, tests, env, Path(tmp))
            except (subprocess.SubprocessError, OSError, zipfile.BadZipFile) as exc:
                rejected[f"crashed: {type(exc).__name__}"] = rejected.get(
                    f"crashed: {type(exc).__name__}", 0) + 1
                continue
        if instance:
            found.append(instance)
            print(f"    {sha[:8]}  kept: {len(instance.f2p)} failing, "
                  f"{len(instance.p2p)} to preserve, {instance.gold_lines} gold line(s) "
                  f"[{band(instance.gold_lines)}]", flush=True)
        else:
            rejected[why] = rejected.get(why, 0) + 1

    # A repository that contributed nothing has to say why. Three of five said
    # nothing at all the first time this ran, and the cause was two missing test
    # dependencies — an environment problem wearing the shape of an empty result.
    for why, count in sorted(rejected.items(), key=lambda kv: -kv[1]):
        print(f"    {count:>3} rejected: {why}", flush=True)
    if not found and rejected:
        worst = max(rejected.items(), key=lambda kv: kv[1])[0]
        note = ", which is installable" if "missing dependency" in worst else ""
        print(f"    {repo.name} contributed nothing; mostly: {worst}{note}", flush=True)
    return found


def lock(corpus: Path, out: Path) -> int:
    """The few kilobytes that identify a corpus, instead of the megabytes of it."""
    rows = json.loads(corpus.read_text(encoding="utf-8"))
    pins = [{"name": r["name"], "origin": r["origin"], "base": r["base"], "fix": r["fix"],
             "tests": sorted(r["hidden_files"])} for r in rows]
    out.write_text(json.dumps(pins, indent=1), encoding="utf-8")
    without = [p["name"] for p in pins if not p["origin"]]
    print(f"{len(pins)} instance(s) pinned -> {out}")
    if without:
        print(f"{len(without)} cannot be rebuilt elsewhere, no origin: {without[:4]}")
        return 1
    return 0


def rebuild(lockfile: Path, where: Path, env: dict[str, str], out: Path) -> int:
    """Reconstruct exactly the pinned instances, or say which are unreachable.

    Refusing is the point. A rebuild that silently mined a nearby commit instead
    would produce a corpus that looks like the original and scores differently,
    which is worse than not rebuilding at all.
    """
    pins = json.loads(lockfile.read_text(encoding="utf-8"))
    found, missing = [], []
    for pin in pins:
        repo = where / Path(pin["origin"]).stem
        if not (repo / ".git").exists():
            missing.append(f"{pin['name']}: no clone of {pin['origin']} at {repo}")
            continue
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            try:
                instance, why = validate(repo, pin["fix"], pin["tests"], env, Path(tmp))
            except (subprocess.SubprocessError, OSError, zipfile.BadZipFile) as exc:
                missing.append(f"{pin['name']}: {type(exc).__name__}")
                continue
        if instance:
            found.append(instance)
            print(f"  {pin['name']}  rebuilt", flush=True)
        else:
            missing.append(f"{pin['name']}: {why}")

    for line in missing:
        print(f"  MISSING {line}")
    out.write_text(json.dumps([i.__dict__ for i in found], indent=1), encoding="utf-8")
    print(f"\n{len(found)} of {len(pins)} rebuilt -> {out}")
    return 1 if missing else show(out)


def show(path: Path) -> int:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not rows:
        print(f"{path} is empty")
        return 1

    repos: dict[str, list[dict]] = {}
    for row in rows:
        repos.setdefault(row["name"].rsplit("-", 1)[0], []).append(row)

    print(f"{len(rows)} instance(s) from {len(repos)} repositor(y/ies)")
    print()
    print(f"{'repository':<16}{'tasks':>6}{'f2p':>6}{'preserved':>11}  bands")
    for name, group in sorted(repos.items()):
        bands = sorted({band(r.get("gold_lines", 0)) for r in group})
        print(f"{name:<16}{len(group):>6}"
              f"{sum(len(r['f2p']) for r in group):>6}"
              f"{sum(len(r.get('p2p', [])) for r in group):>11}  {', '.join(bands)}")

    print()
    print(f"{'band':<14}{'tasks':>6}   what it means")
    meaning = {"one-liner": "the maintainer changed one to three lines of source",
               "small": "four to twenty lines",
               "substantial": "more than twenty lines",
               "empty": "no source change recorded"}
    for name, _, _ in (*BANDS, ("empty", 0, 0)):
        count = sum(1 for r in rows if band(r.get("gold_lines", 0)) == name)
        if count:
            print(f"{name:<14}{count:>6}   {meaning[name]}")

    missing = [r["name"] for r in rows if not r.get("p2p")]
    if missing:
        print(f"\n{len(missing)} instance(s) carry no preservation set: {missing[:4]}")
    unpinned = [r["name"] for r in rows if not r.get("origin")]
    if unpinned:
        print(f"{len(unpinned)} instance(s) record no origin and are tied to this disk")
    print()
    print("Bands are labels. Nothing was dropped for being easy or hard, because a")
    print("corpus filtered around the mechanism under test is not evidence about it.")
    return 0


def main(argv: list[str]) -> int:
    def option(flag, default):
        return argv[argv.index(flag) + 1] if flag in argv else default

    if "--show" in argv:
        return show(Path(option("--show", "corpus.json")))
    if "--lock" in argv:
        return lock(Path(option("--lock", "corpus.json")), Path(option("--out", "corpus.lock")))
    if "--rebuild" in argv:
        where = Path(option("--repos", ""))
        if not where.is_dir():
            print(__doc__)
            return 1
        return rebuild(Path(option("--rebuild", "corpus.lock")), where,
                       {"PYTHONPATH": option("--pythonpath", "src")},
                       Path(option("--out", "corpus.json")))

    where = Path(option("--repos", ""))
    if not where.is_dir():
        print(__doc__)
        return 1
    repos = sorted(d for d in where.iterdir() if (d / ".git").exists())
    only = option("--only", "")
    if only:
        repos = [d for d in repos if d.name in only.split(",")]
    if not repos:
        print(f"no git repositories under {where}")
        return 1

    env = {"PYTHONPATH": option("--pythonpath", "src")}
    want, limit = int(option("--want", "6")), int(option("--limit", "200"))
    print(f"mining {len(repos)} repositor(y/ies), up to {want} instance(s) from each")

    found: list[Instance] = []
    for repo in repos:
        found.extend(mine_repo(repo, want, limit, env,
                               option("--source-dir", "src"), option("--test-dir", "tests")))

    out = Path(option("--out", "corpus.json"))
    out.write_text(json.dumps([i.__dict__ for i in found], indent=1), encoding="utf-8")
    print(f"\n{len(found)} instance(s) -> {out}")
    return show(out)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
