"""Blind-review packets for the 27 B7 survivors.

Re-seeds each task with the gold patch, re-derives the chosen mutants with the
exact code B7 ran, and ASSERTS they match results/b7-mutants/mutants.json item
for item - so the raters judge the mutants that were counted, not a lookalike.
Each packet shows the real enclosing function with the mutated line marked.
"""
from __future__ import annotations

import ast
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "E:/ElevenPowers")
sys.path.insert(0, "E:/ElevenPowers/results/b7-mutants")
import probe  # noqa: E402
from probe import MAX_MUTANTS, changed_source, sites  # noqa: E402

from eval.live import _seed_git, base_tree  # noqa: E402
from eval.mined import load as load_mined  # noqa: E402

S = Path("C:/Users/Satyam/AppData/Local/Temp/claude/e--ElevenPowers/cf4ea1a0-0d66-483c-af19-d5e4658f485a/scratchpad")
REPORT = json.loads(Path("E:/ElevenPowers/results/b7-mutants/mutants.json").read_text(encoding="utf-8"))
ROWS = {r["name"]: r for r in json.loads(Path("E:/ep-corpus/prevalence.json").read_text(encoding="utf-8"))}
TASKS = {t.name: t for t in load_mined()}


def context(src: str, line: int) -> str:
    tree = ast.parse(src)
    best = None
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if n.lineno <= line <= (n.end_lineno or n.lineno):
                if best is None or n.lineno >= best.lineno:
                    best = n
    lines = src.splitlines()
    if best is not None:
        lo, hi = best.lineno, best.end_lineno or best.lineno
        if hi - lo > 70:
            lo, hi = max(best.lineno, line - 30), min(hi, line + 30)
    else:
        lo, hi = max(1, line - 15), min(len(lines), line + 15)
    out = []
    for i in range(lo, hi + 1):
        mark = ">>" if i == line else "  "
        out.append(f"{mark}{i:5d} | {lines[i - 1]}")
    return "\n".join(out)


items = []
with tempfile.TemporaryDirectory(prefix="ep-packets-", ignore_cleanup_errors=True) as tmp:
    for r in REPORT:
        survivors = [i for i, m in enumerate(r.get("mutants", [])) if m["verdict"] == "SURVIVED"]
        if not survivors:
            continue
        task = TASKS[r["task"]]
        root = Path(tmp) / task.name
        root.mkdir(parents=True)
        base_tree(task, root)
        _seed_git(root)
        base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip()
        gold = subprocess.run(["git", "-C", task.source["repo"], "show", ROWS[task.name]["fix"]], capture_output=True)
        subprocess.run(["git", "-C", str(root), "apply", "--3way", "-"], input=gold.stdout, capture_output=True, check=True)
        changed = changed_source(root, base)
        candidates = []
        for rel, lines in sorted(changed.items()):
            for key, name in sites((root / rel).read_text(encoding="utf-8"), lines):
                candidates.append((rel, key, name))
        step = max(1, len(candidates) // MAX_MUTANTS)
        chosen = candidates[::step][:MAX_MUTANTS]
        recorded = [(m["file"], m["op"]) for m in r["mutants"]]
        derived = [(rel, name) for rel, _, name in chosen]
        assert recorded == derived, f"{task.name}: re-derived mutants differ from what B7 ran\n{recorded}\n{derived}"
        for i in survivors:
            rel, key, name = chosen[i]
            src = (root / rel).read_text(encoding="utf-8")
            items.append({"task": task.name, "file": rel, "op": name, "line": key[1],
                          "mutation": r["mutants"][i]["diff"], "context": context(src, key[1]),
                          "b7_index": i})

print(f"re-derived and matched: {len(items)} survivors (expect 27)")
random.Random(20260924).shuffle(items)
for n, it in enumerate(items, 1):
    it["id"] = f"M{n:02d}"

RUBRIC = """Classify each mutant. A mutant is the original code with ONE small change
(shown as `original  ->  mutated`). The line marked `>>` is where it was made.

  EQUIVALENT  - no input, call sequence or environment could make the mutated
                program behave observably differently from the original.
  TRIVIAL     - behaviour can differ, but only in a way no reasonable caller or
                user would care about (message wording, a warning's stacklevel,
                performance, a value nothing reads).
  MEANINGFUL  - some reachable input produces observably different behaviour a
                caller or user would care about: a wrong result, a crash, a
                missing side effect, a different exception, a changed default.
  UNSURE      - you cannot decide from the code shown.

Judge from the code alone. Give one short sentence of reasoning per item."""

packet = ["# Blind review packet — 27 mutants\n", RUBRIC, ""]
for it in items:
    packet += [f"## {it['id']}  ({it['file']}, operator: {it['op']})",
               f"Mutation at line {it['line']}:  `{it['mutation']}`", "", "```python",
               it["context"], "```", ""]
(S / "blind_packet.md").write_text("\n".join(packet), encoding="utf-8")
(S / "blind_key.json").write_text(json.dumps(items, indent=1), encoding="utf-8")
print("packet:", S / "blind_packet.md", f"({len(packet)} lines)")
