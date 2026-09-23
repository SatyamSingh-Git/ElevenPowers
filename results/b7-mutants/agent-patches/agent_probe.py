"""SPIKE - the B7 probe pointed at AGENTS' patches instead of the gold one.

Same operators, same three traps, same controls, imported from
results/b7-mutants/probe.py so nothing that was validated there is re-typed.
The patch under test is a RESOLVED candidate from an earlier paid sweep, one per
task, applied the way the grader applies it.

One control changes meaning. For the gold patch, reverting the change and
seeing it survive meant the harness was not reading the source. For an agent's
patch the harness is already validated on the same task, so a surviving revert
is the finding itself: the tests in the tree (the repo's plus whatever the agent
wrote) cannot tell the change from its absence. That is VACUOUS in stress.py's
sense, and it is recorded rather than treated as a failure.

    python agent_probe.py 0/3 out0.json
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, "E:/ElevenPowers")
sys.path.insert(0, "E:/ElevenPowers/results/b7-mutants")
import probe  # noqa: E402  (sets EP_MINED and the import path)
from probe import MAX_MUTANTS, changed_source, mutate, sites, suite, _show  # noqa: E402

from eval.bundle import apply_patch  # noqa: E402
from eval.live import _seed_git, base_tree  # noqa: E402
from eval.mined import load as load_mined  # noqa: E402

RESULTS = Path("E:/ElevenPowers/results")
PREFER = ["b4-discriminate", "prevalence/bundles/", "b3-stress", "b5-bypass",
          "bundles-A", "bundles-B", "chunks", "closedbook"]


def pick() -> dict:
    prev = {r["name"] for r in json.loads(Path("E:/ep-corpus/prevalence.json").read_text(encoding="utf-8"))}
    best = {}
    for m in RESULTS.rglob("manifest.json"):
        b = m.parent
        g, p = b / "grade.json", b / "patch.diff"
        if not (g.exists() and p.exists()) or p.stat().st_size == 0:
            continue
        man = json.loads(m.read_text(encoding="utf-8"))
        gr = json.loads(g.read_text(encoding="utf-8"))
        t = man.get("task")
        if t not in prev or gr.get("outcome") != "resolved":
            continue
        rel = str(b.relative_to(RESULTS)).replace("\\", "/")
        rank = next((i for i, k in enumerate(PREFER) if rel.startswith(k)), 99)
        cand = (rank, rel, man.get("model_asked") or man.get("model"), b)
        if t not in best or cand[:2] < best[t][:2]:
            best[t] = cand
    return best


def git(root, *a):
    return subprocess.run(["git", *a], cwd=root, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def one(task, bundle: Path, hold: Path) -> dict:
    root = hold / task.name
    root.mkdir(parents=True, exist_ok=True)
    base_tree(task, root)
    _seed_git(root)
    base = git(root, "rev-parse", "HEAD").stdout.strip()
    patch = (bundle / "patch.diff").read_bytes().decode("utf-8", errors="replace")
    trouble = apply_patch(root, patch)
    if trouble:
        return {"why": f"agent patch did not apply: {str(trouble)[:200]}"}

    env = {**os.environ, **{k: str(v) for k, v in (task.source.get("env") or {}).items()}}
    red, timed, code = suite(root, env, [])
    if timed:
        return {"why": "baseline suite timed out"}
    deselect = [a for rid in sorted(red) for a in ("--deselect", rid)]
    still, timed, code = suite(root, env, deselect)
    if still or code not in (0, 5):
        return {"why": f"baseline not green after deselect ({len(still)} red, exit {code})"}

    changed = changed_source(root, base)
    if not changed:
        return {"why": "agent patch changed no source lines"}

    # Revert: the agent's source change undone, its tests kept.
    saved = {rel: (root / rel).read_text(encoding="utf-8") for rel in changed}
    for rel in changed:
        old = git(root, "show", f"{base}:{rel}")
        if old.returncode == 0:
            (root / rel).write_text(old.stdout, encoding="utf-8")
    try:
        failing, timed, code = suite(root, env, deselect + ["-x"])
    finally:
        for rel, body in saved.items():
            (root / rel).write_text(body, encoding="utf-8")
    revert_killed = timed or bool(failing) or code not in (0, 5)

    # Survive control keeps its meaning exactly.
    first = sorted(changed)[0]
    body = saved[first]
    (root / first).write_text(body + "\n_ep_probe_noop = 0\n", encoding="utf-8")
    try:
        failing, timed, code = suite(root, env, deselect + ["-x"])
    finally:
        (root / first).write_text(body, encoding="utf-8")
    if timed or failing or code not in (0, 5):
        return {"why": "CONTROL FAILED survive_ok=False - harness result, not a finding"}

    candidates = []
    for rel, lines in sorted(changed.items()):
        src = (root / rel).read_text(encoding="utf-8")
        for key, name in sites(src, lines):
            candidates.append((rel, key, name))
    step = max(1, len(candidates) // MAX_MUTANTS)
    chosen = candidates[::step][:MAX_MUTANTS]

    results = []
    import ast
    for rel, key, name in chosen:
        path = root / rel
        original = path.read_text(encoding="utf-8")
        mutated = mutate(original, key, name)
        if mutated is None or mutated == ast.unparse(ast.parse(original)):
            results.append({"file": rel, "op": name, "key": list(key), "verdict": "not generated"})
            continue
        path.write_text(mutated, encoding="utf-8")
        try:
            failing, timed, code = suite(root, env, deselect + ["-x"])
        finally:
            path.write_text(original, encoding="utf-8")
        verdict = ("killed (timeout)" if timed else
                   "killed" if (failing or code not in (0, 5)) else "SURVIVED")
        results.append({"file": rel, "op": name, "key": list(key), "verdict": verdict,
                        "diff": _show(original, mutated)})
    tests_changed = [p for p in git(root, "diff", "--name-only", base).stdout.split()
                     if p.endswith(".py") and p not in changed]
    return {"revert_killed": revert_killed, "baseline_red": len(red),
            "changed": {k: len(v) for k, v in changed.items()},
            "tests_in_patch": tests_changed, "sites": len(candidates), "mutants": results}


def main():
    shard, n = map(int, sys.argv[1].split("/"))
    out = Path(sys.argv[2])
    chosen = pick()
    tasks = {t.name: t for t in load_mined()}
    names = sorted(chosen)[shard::n]
    report = []
    with tempfile.TemporaryDirectory(prefix=f"ep-agent-{shard}-", ignore_cleanup_errors=True) as tmp:
        for name in names:
            rank, rel, model, bundle = chosen[name]
            t0 = time.time()
            try:
                r = one(tasks[name], bundle, Path(tmp))
            except Exception as e:  # noqa: BLE001
                r = {"why": f"{type(e).__name__}: {e}"}
            r.update({"task": name, "bundle": rel, "model": model, "seconds": round(time.time() - t0)})
            report.append(r)
            ms = r.get("mutants", [])
            live = sum(1 for m in ms if m["verdict"] == "SURVIVED")
            made = sum(1 for m in ms if m["verdict"] != "not generated")
            said = r.get("why") or (f"{live}/{made} survived  revert_killed={r['revert_killed']}  "
                                    f"tests_in_patch={len(r['tests_in_patch'])}")
            print(f"{name:24s} {model or '?':18s} {said}  ({r['seconds']}s)", flush=True)
            out.write_text(json.dumps(report, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
