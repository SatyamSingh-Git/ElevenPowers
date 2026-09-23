"""B8 SPIKE - does telling an agent WHICH lines are unpinned make it pin them?

Paired, per task, same starting tree (base + gold patch, committed):

  generic  - "parts of this change could be broken without any test noticing;
              strengthen the tests"
  mutants  - the same prompt PLUS the exact list of surviving mutants

Then the B7 probe is re-run on the SAME chosen mutants. The question is not
whether the agent writes tests - it will - but whether the specific list makes
the tests pin more of the change than asking does.

Guards, because an agent told "make these mutants fail" has easy ways to cheat:
  - source must not change (restored and recorded if it does, so mutants apply
    to identical code)
  - every originally KILLED mutant must stay killed (a weakened test shows up)
  - new tests are scanned for reading source text rather than testing behaviour
  - baseline + survive control re-run, so a failing or flaky new test cannot
    manufacture kills
"""
from __future__ import annotations

import ast
import concurrent.futures as cf
import dataclasses
import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, "E:/ElevenPowers")
sys.path.insert(0, "E:/ElevenPowers/results/b7-mutants")
import probe  # noqa: E402
from probe import MAX_MUTANTS, changed_source, mutate, sites, suite  # noqa: E402

from core.surface import TEST_NAME  # noqa: E402
from eval.live import _seed_git, base_tree, drive  # noqa: E402
from eval.mined import load as load_mined  # noqa: E402

S = Path("C:/Users/Satyam/AppData/Local/Temp/claude/e--ElevenPowers/cf4ea1a0-0d66-483c-af19-d5e4658f485a/scratchpad")
HOLD = S / "b8-work"
OUT = S / "b8"
MODEL, EFFORT, BUDGET = "claude-opus-5-5", "high", 15.0
REPORT = json.loads(Path("E:/ElevenPowers/results/b7-mutants/mutants.json").read_text(encoding="utf-8"))
ROWS = {r["name"]: r for r in json.loads(Path("E:/ep-corpus/prevalence.json").read_text(encoding="utf-8"))}
TASKS = {t.name: t for t in load_mined()}
LOCK = threading.Lock()
TAUTOLOGY = re.compile(r"inspect\.getsource|ast\.parse|getsourcelines|read_text\(|open\([^)]*\.py|__file__")

COMMON = """The most recent commit in this repository (see it with `git show HEAD`) is a change to {files}.

Its tests are not thorough enough: parts of the code that commit changed could be broken without any existing test noticing.

Strengthen the test suite so that it would catch mistakes in the lines that commit changed.

Rules:
- Only add or modify test files under tests/. Do not modify any other file.
- Every test you add must pass on the code exactly as it is now.
- Run the tests (`python -m pytest tests -q`) to confirm they pass before you finish.
"""

SPECIFIC = """
Specifically, each of the following modifications to the changed code currently goes unnoticed by every existing test. Add tests that would fail if any of them were made:
{items}
"""


def git(root, *a, check=False):
    return subprocess.run(["git", *a], cwd=root, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", check=check)


def log(msg):
    with LOCK:
        print(time.strftime("%H:%M:%S"), msg, flush=True)


def prepare(task, arm):
    root = HOLD / f"{task.name}--{arm}"
    root.mkdir(parents=True, exist_ok=False)
    base_tree(task, root)
    _seed_git(root)
    base = git(root, "rev-parse", "HEAD").stdout.strip()
    gold = subprocess.run(["git", "-C", task.source["repo"], "show", ROWS[task.name]["fix"]], capture_output=True)
    subprocess.run(["git", "-C", str(root), "apply", "--3way", "-"], input=gold.stdout, capture_output=True, check=True)
    changed = changed_source(root, base)
    git(root, "add", "-A")
    git(root, "-c", "user.email=b8@example.invalid", "-c", "user.name=b8", "commit", "-qm",
        "gold change under test", check=True)
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    candidates = []
    for rel, lines in sorted(changed.items()):
        for key, name in sites((root / rel).read_text(encoding="utf-8"), lines):
            candidates.append((rel, key, name))
    step = max(1, len(candidates) // MAX_MUTANTS)
    chosen = candidates[::step][:MAX_MUTANTS]
    return root, base, start, changed, chosen


def run_mutants(root, env, chosen):
    red, timed, code = suite(root, env, [])
    deselect = [a for rid in sorted(red) for a in ("--deselect", rid)]
    still, timed, code = suite(root, env, deselect)
    baseline_green = not still and code in (0, 5)
    first = chosen[0][0]
    body = (root / first).read_text(encoding="utf-8")
    (root / first).write_text(body + "\n_ep_probe_noop = 0\n", encoding="utf-8")
    try:
        failing, t2, c2 = suite(root, env, deselect + ["-x"])
    finally:
        (root / first).write_text(body, encoding="utf-8")
    survive_ok = not t2 and not failing and c2 in (0, 5)
    verdicts = []
    for rel, key, name in chosen:
        path = root / rel
        original = path.read_text(encoding="utf-8")
        mutated = mutate(original, key, name)
        if mutated is None or mutated == ast.unparse(ast.parse(original)):
            verdicts.append("not generated")
            continue
        path.write_text(mutated, encoding="utf-8")
        try:
            failing, t3, c3 = suite(root, env, deselect + ["-x"])
        finally:
            path.write_text(original, encoding="utf-8")
        verdicts.append("killed (timeout)" if t3 else "killed" if (failing or c3 not in (0, 5)) else "SURVIVED")
    return {"baseline_red_after": sorted(red), "baseline_green": baseline_green,
            "survive_ok": survive_ok, "verdicts": verdicts}


def one(task_name, arm):
    task = TASKS[task_name]
    record = next(r for r in REPORT if r["task"] == task_name)
    t0 = time.time()
    try:
        root, base, start, changed, chosen = prepare(task, arm)
        recorded = [(m["file"], m["op"]) for m in record["mutants"]]
        assert recorded == [(rel, name) for rel, _, name in chosen], "mutants differ from B7"
        before = [m["verdict"] for m in record["mutants"]]
        prompt = COMMON.format(files=", ".join(sorted(changed)))
        if arm == "mutants":
            items = [f"{n}. {rel} line {key[1]}: `{m['diff']}`"
                     for n, ((rel, key, _), m) in enumerate(
                         [(c, m) for c, m in zip(chosen, record["mutants"]) if m["verdict"] == "SURVIVED"], 1)]
            prompt += SPECIFIC.format(items="\n".join(items))
        log(f"start {task_name} {arm}")
        answer, elapsed = drive(dataclasses.replace(task, prompt=prompt), root, MODEL, "vanilla", EFFORT, BUDGET)
        log(f"agent done {task_name} {arm}: ${float(answer.get('total_cost_usd') or 0):.2f} "
            f"turns={answer.get('num_turns')} error={answer.get('is_error')} {round(elapsed)}s")

        status = git(root, "status", "--porcelain").stdout.splitlines()
        touched = sorted({ln[3:].strip().strip('"') for ln in status})
        tests = [p for p in touched if p.startswith("tests/") or TEST_NAME.search(p)]
        other = [p for p in touched if p not in tests and not p.startswith(".")]
        restored = []
        for p in other:
            if git(root, "cat-file", "-e", f"{start}:{p}").returncode == 0:
                git(root, "checkout", start, "--", p)
                restored.append(p)
        test_diff = git(root, "diff", start, "--", "tests").stdout
        for p in tests:
            if git(root, "ls-files", "--error-unmatch", p).returncode != 0 and (root / p).is_file():
                test_diff += (root / p).read_text(encoding="utf-8", errors="replace")
        tautology = sorted(set(TAUTOLOGY.findall(test_diff)))
        env = {**os.environ, **{k: str(v) for k, v in (task.source.get("env") or {}).items()}}
        after = run_mutants(root, env, chosen)
        pairs = list(zip(before, after["verdicts"]))
        result = {
            "task": task_name, "arm": arm, "model": MODEL, "effort": EFFORT,
            "cost": float(answer.get("total_cost_usd") or 0.0), "turns": answer.get("num_turns"),
            "is_error": answer.get("is_error"), "seconds": round(time.time() - t0),
            "tests_touched": tests, "source_touched_and_restored": restored, "other_touched": other,
            "tautology_markers": tautology, "test_diff_lines": test_diff.count("\n"),
            "baseline_green_after": after["baseline_green"], "survive_ok_after": after["survive_ok"],
            "new_red_on_unmutated_tree": len(after["baseline_red_after"]),
            "before": before, "after": after["verdicts"],
            "survivors_before": sum(b == "SURVIVED" for b in before),
            "survivors_now_killed": sum(b == "SURVIVED" and a.startswith("killed") for b, a in pairs),
            "killed_now_survived": sum(b.startswith("killed") and a == "SURVIVED" for b, a in pairs),
        }
    except Exception as e:  # noqa: BLE001
        result = {"task": task_name, "arm": arm, "why": f"{type(e).__name__}: {e}",
                  "seconds": round(time.time() - t0)}
    (OUT / f"{task_name}--{arm}.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    log(f"DONE {task_name} {arm}: " + (result.get("why") or
        f"{result['survivors_now_killed']}/{result['survivors_before']} survivors now killed, "
        f"{result['killed_now_survived']} un-killed, src_restored={len(result['source_touched_and_restored'])}, "
        f"tautology={result['tautology_markers']}, ${result['cost']:.2f}"))
    return result


def main():
    HOLD.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    names = [r["task"] for r in REPORT if any(m["verdict"] == "SURVIVED" for m in r.get("mutants", []))]
    jobs = [(n, arm) for n in names for arm in ("generic", "mutants")]
    log(f"{len(jobs)} runs: {len(names)} tasks x 2 arms, {MODEL} effort={EFFORT} cap=${BUDGET}")
    with cf.ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        list(pool.map(lambda j: one(*j), jobs))
    log("all done")


if __name__ == "__main__":
    main()
