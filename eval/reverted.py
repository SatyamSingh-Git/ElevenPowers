"""Would our own passing evidence have passed without the change?

    python -m eval.reverted --bundles results --out results/reverted

P22, asked of saved runs for nothing. `core/stress.py` asks it live, of the
project's *declared* command, and has answered on 26 saved ledgers: 25
discriminating, one vacuous. This asks the records the agents produced
themselves, which is where weak evidence would live if it lives anywhere.

**One method, both directions, per bundle.** The base commit is materialised
twice the way the harness built it. *Forward*: the saved patch applied; the
recorded check must pass there today, or nothing it says about the old tree can
be trusted. *Adversarial*: the old source with the patch's test files laid over
it, which is stress's method and the only way an agent-written test can be
asked at all. Passing there is `VACUOUS`. Failing tests there is
`DISCRIMINATES`, and so is a carried test that cannot import the old code -- the
common shape of a test for new behaviour -- labelled separately so the two can
be read apart. Anything else is `UNCHECKABLE` with its reason.

**Why the forward run is not optional.** Re-collecting the 22 corpus base trees
under pytest 9.1.1 on 2026-10-10 failed 18: attrs for a missing `hypothesis`,
click on a file its saved patch never touches. Without the forward control that
drift would have been counted as discrimination.

**What is re-run.** Only `python -m pytest` with the workspace prefix and output
shaping removed, and nothing that could write, chain, substitute or point at
the old workspace -- a separately qualified policy, because stress.py rightly
refuses recorded shell lines in the runtime. Everything else stays in the
funnel with its reason.

**Toolchain.** A run recorded since `fafe61a` carries its runner and package
set; one that differs from today's is refused without being run. Earlier runs
recorded neither, so their results are reported as their own stratum and never
pooled with matched ones. Their only qualification is the forward control.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from functools import cache
from pathlib import Path

from core.evidence import Kind, SourceScan
from core.parsers import parse
from core.stress import DISCRIMINATES, UNCHECKABLE, VACUOUS
from core.surface import TEST_NAME

from .bundle import apply_patch, read
from .live import environment, materialise
from .task import Task

TIMEOUT = 900

WORKSPACE = re.compile(r'^cd\s+"[^"]*"\s*&&\s*')
SHAPING = re.compile(r"(\s+2>&1)?(\s*\|\s*tail\s+-n?\s*\d+)?\s*$")
CHECK = re.compile(r"^python -m pytest(\s|$)")
UNSAFE = re.compile(r"[;&|<>`$\n]")
ABSOLUTE = re.compile(r'(^|\s|["\'])([A-Za-z]:[\\/]|/)')
# A file that would not collect, and not a setup error: core/stress.py's
# COLLECT_ERROR also matches `ERROR tests/test_x.py::test_a`, a fixture that
# raised, which says nothing about whether the old code can be imported.
NOT_COLLECTED = re.compile(r"^ERROR\s+(\S+?\.py)(?=\s|$)", re.MULTILINE)
TOUCHED = re.compile(r"^(?:\+\+\+ b|--- a)/(.+?)\s*$", re.MULTILINE)


def runnable(command: str) -> tuple[str | None, str]:
    """The check a recorded command ran, if it can be re-run safely elsewhere."""
    check = SHAPING.sub("", WORKSPACE.sub("", command.strip()))
    if not CHECK.match(check):
        return None, "not a pytest run"
    if UNSAFE.search(check):
        return None, "could write, chain or substitute"
    if ABSOLUTE.search(check):
        return None, "names its old workspace"
    if "--version" in check.split():
        return None, "runs no tests"
    return check, ""


def _ran_tests(record: dict) -> bool:
    return (record.get("result") == "pass" and record.get("kind") in ("test", "test_suite")
            and (record.get("passed") or 0) > 0)


def _evidence(bundle: Path) -> list[dict]:
    ledger = bundle / "ledger.json"
    return json.loads(ledger.read_text(encoding="utf-8")).get("evidence", []) if ledger.exists() else []


def funnel(bundles: list[Path]) -> dict:
    """Every record, and where each one left the measurement."""
    counts = Counter()
    excluded = Counter()
    for bundle in bundles:
        for record in _evidence(bundle):
            counts["records"] += 1
            if record.get("result") != "pass":
                excluded["not passing"] += 1
                continue
            counts["passing"] += 1
            if not _ran_tests(record):
                excluded["not a test record that ran tests"] += 1
                continue
            counts["passing test records that ran tests"] += 1
            check, why = runnable(record.get("command") or "")
            if check is None:
                excluded[f"not re-executable: {why}"] += 1
                continue
            counts["re-executable"] += 1
    return {**{k: counts[k] for k in ("records", "passing", "passing test records that ran tests",
                                      "re-executable")},
            "excluded": dict(excluded.most_common())}


@cache
def _today() -> dict:
    return environment()


def _toolchain(manifest: dict) -> tuple[str, str]:
    recorded = manifest.get("environment") or {}
    if "tools" not in recorded:
        return "unrecorded", ""
    then, now = recorded["tools"].get("pytest"), _today()["tools"]["pytest"]
    if then != now:
        return "differs", (f"toolchain differs: pytest {then.get('version') or then.get('state')} "
                           f"recorded, {now['version'] or now['state']} now") if then else \
            "toolchain differs: pytest not recorded"
    absent = sorted(set(recorded.get("packages") or ()) - set(_today()["packages"]))
    if absent:
        return "differs", f"toolchain differs: {len(absent)} recorded packages absent now, e.g. {absent[0]}"
    return "matched", ""


def _trees(manifest: dict, patch: str, hold: Path) -> tuple[Path, Path, set[str], str]:
    """The patched tree, and the old source carrying the patch's tests."""
    task = Task(name=manifest["task"], prompt="", files={}, hidden="", why="",
                source={**manifest["base"], "env": manifest.get("env") or {}})
    # Separate parents: materialise caches its archive beside the tree.
    forward, before = hold / "forward" / "tree", hold / "before" / "tree"
    for root in (forward, before):
        root.mkdir(parents=True)
        materialise(task, root)
    complaint = apply_patch(forward, patch)
    if complaint:
        return forward, before, set(), f"patch does not apply: {complaint[:200]}"
    carried = {p for p in TOUCHED.findall(patch) if TEST_NAME.search(p)}
    for rel in carried:
        if (forward / rel).is_file():
            (before / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(forward / rel, before / rel)
        else:
            (before / rel).unlink(missing_ok=True)
    return forward, before, carried, ""


def _run(check: str, root: Path, env: dict) -> tuple[int, str, int, int] | None:
    command = f'"{sys.executable}"' + check[len("python"):]
    try:
        done = subprocess.run(command, shell=True, cwd=root, env=env, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return None
    output = (done.stdout or "") + (done.stderr or "")
    suites = [r for r in parse(check, output, done.returncode, root, snapshot=(SourceScan(), ""))
              if r.kind is Kind.SUITE]
    passed, failed = (suites[0].passed, suites[0].failed) if suites else (0, 0)
    return done.returncode, output, passed, failed


def _gist(output: str) -> str:
    lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    errors = [ln for ln in lines if ln.startswith(("E ", "ERROR"))]
    return (errors[:1] + lines[-1:])[0][:160] if lines else "no output"


def _classify(check: str, forward: Path, before: Path, carried: set[str], env: dict) -> dict:
    ahead = _run(check, forward, env)
    if ahead is None:
        return {"verdict": UNCHECKABLE, "how": "", "why": "timed out on the patched tree"}
    code, output, passed, _ = ahead
    if code != 0 or passed <= 0:
        return {"verdict": UNCHECKABLE, "how": "",
                "why": f"does not reproduce on the patched tree: {_gist(output)}"}
    behind = _run(check, before, env)
    if behind is None:
        return {"verdict": UNCHECKABLE, "how": "", "why": "timed out on the old tree"}
    code, output, passed, failed = behind
    if code == 0 and passed > 0:
        return {"verdict": VACUOUS, "how": "", "why": ""}
    # Before the failure count: the runtime's parser reads pytest's "1 error"
    # as a failed test, so an environment that cannot collect would otherwise
    # be scored as a check that discriminates.
    broken = {e.replace("\\", "/") for e in NOT_COLLECTED.findall(output)}
    if broken:
        if broken <= carried:
            return {"verdict": DISCRIMINATES, "how": "carried test cannot import the old code", "why": ""}
    elif failed > 0:
        return {"verdict": DISCRIMINATES, "how": "failing test", "why": ""}
    return {"verdict": UNCHECKABLE, "how": "", "why": f"did not run on the old tree: {_gist(output)}"}


def measure(bundle: Path, hold: Path) -> list[dict]:
    """One row per distinct re-executable passing check in a bundle."""
    units = Counter()
    for record in _evidence(bundle):
        if _ran_tests(record):
            check, _ = runnable(record.get("command") or "")
            if check:
                units[check] += 1
    if not units:
        return []
    saved = read(bundle)
    manifest = saved["manifest"]
    toolchain, why = _toolchain(manifest)
    rows = [{"bundle": bundle.name, "task": manifest["task"], "command": check, "records": n,
             "toolchain": toolchain} for check, n in sorted(units.items())]
    if toolchain == "differs":
        return [{**row, "verdict": UNCHECKABLE, "how": "", "why": why} for row in rows]
    try:
        forward, before, carried, problem = _trees(manifest, saved["patch"], hold)
        if problem:
            return [{**row, "verdict": UNCHECKABLE, "how": "", "why": problem} for row in rows]
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
               **{k: str(v) for k, v in (manifest.get("env") or {}).items()}}
        return [{**row, **_classify(row["command"], forward, before, carried, env)} for row in rows]
    finally:
        shutil.rmtree(hold, ignore_errors=True)


def main(argv: list[str]) -> int:
    import argparse
    import tempfile

    options = argparse.ArgumentParser(prog="python -m eval.reverted")
    options.add_argument("--bundles", type=Path, default=Path("results"))
    options.add_argument("--out", type=Path, required=True)
    options.add_argument("--limit", type=int, default=0, help="bundles to measure; 0 is all")
    args = options.parse_args(argv)

    # Any directory holding a ledger. Globbing `bundles/` found 54 of 106: the
    # chunked sweeps save to `bundles-chunk1/`, and nothing said they were missed.
    bundles = sorted({p.parent for p in args.bundles.glob("**/ledger.json")})
    measured = bundles[:args.limit] if args.limit else bundles
    args.out.mkdir(parents=True, exist_ok=True)
    rows_file = args.out / "rows.jsonl"
    done = {json.loads(ln)["path"] for ln in rows_file.read_text(encoding="utf-8").splitlines()
            } if rows_file.exists() else set()
    with tempfile.TemporaryDirectory(prefix="ep-reverted-") as hold:
        for index, bundle in enumerate(measured, 1):
            # Keyed by path: the same run name recurs across sweep directories.
            path = bundle.relative_to(args.bundles).as_posix()
            if path in done:
                continue
            rows = measure(bundle, Path(hold) / str(index))
            # One line per bundle, appended as it finishes, so an interrupted
            # sweep resumes rather than starts over. A bundle with nothing to
            # measure still gets a line, or it would be retried forever.
            with rows_file.open("a", encoding="utf-8") as out:
                out.write(json.dumps({"path": path, "rows": rows}) + "\n")
            print(f"[{index}/{len(measured)}] {bundle.name}: "
                  + (", ".join(f"{r['verdict'] or 'unknown'}" for r in rows) or "nothing to measure"),
                  flush=True)

    rows = [r for ln in rows_file.read_text(encoding="utf-8").splitlines() for r in json.loads(ln)["rows"]]
    verdicts = Counter((r["toolchain"], r["verdict"], r["how"]) for r in rows)
    summary = {
        "method": "forward on base+patch, adversarial on base+carried tests; core/stress.py states",
        "toolchain_today": _today()["tools"],
        "bundles": len(measured),
        "funnel": funnel(measured),
        "checks": len(rows),
        "verdicts": [{"toolchain": t, "verdict": v, "how": h, "checks": n}
                     for (t, v, h), n in sorted(verdicts.items())],
        "uncheckable": dict(Counter(r["why"].split(":")[0] for r in rows
                                    if r["verdict"] == UNCHECKABLE).most_common()),
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
