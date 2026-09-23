"""SPIKE - NOT product code. Kept only so results/b7-mutants/ can be reproduced.

Answers PLAN §5.16's gate question, nothing more. It is not imported by
anything in core/ or eval/, and building §5.16 properly means borrowing an
engine (build-on.md names mutmut and cosmic-ray), not promoting this file.

    python results/b7-mutants/probe.py            # all 16, ~22 minutes, $0

    For each corpus task, with the GOLD patch applied: generate mutants confined
    to the source lines the patch changed, run the task's own suite, and ask how
    often a mutant SURVIVES.

Three traps this is built to avoid, each one learned this week:

- The declared environment is applied (PYTHONPATH=src). Without it the suite
  imports the installed release, not the mutated source, and every mutant
  "survives" because nothing ran against it.
- Node ids go in an argument list, never through a shell. `test_x[<lambda>0]`
  killed a shell command outright on 2026-09-22.
- A baseline comes first. Tests already failing on the patched tree are
  deselected, so a mutant is only "killed" by a NEW failure. Otherwise a task
  with pre-existing red would report every mutant killed.
"""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, "E:/ElevenPowers")
CORPUS = Path("E:/ep-corpus/prevalence.json")
os.environ["EP_MINED"] = str(CORPUS)

from core.surface import TEST_NAME
from eval.live import _seed_git, base_tree
from eval.mined import load as load_mined

MAX_MUTANTS = int(os.environ.get("MAX_MUTANTS", "8"))
TIMEOUT = 240
FAILED = re.compile(r"^(?:FAILED|ERROR)\s+(\S+)", re.MULTILINE)


# --- mutation operators, applied to one node -------------------------------

SWAP_CMP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
            ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Is: ast.IsNot,
            ast.IsNot: ast.Is, ast.In: ast.NotIn, ast.NotIn: ast.In}
SWAP_BIN = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv}


def operators(node):
    """(name, apply) pairs available at this node. apply mutates in place."""
    out = []
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in SWAP_CMP:
        def f(n, _t=SWAP_CMP[type(node.ops[0])]):
            n.ops = [_t()]
        out.append((f"cmp {type(node.ops[0]).__name__}->{SWAP_CMP[type(node.ops[0])].__name__}", f))
    if isinstance(node, ast.BoolOp):
        other = ast.Or if isinstance(node.op, ast.And) else ast.And
        def f(n, _o=other):
            n.op = _o()
        out.append((f"bool {type(node.op).__name__}->{other.__name__}", f))
    if isinstance(node, (ast.If, ast.While, ast.IfExp)):
        def f(n):
            n.test = ast.UnaryOp(op=ast.Not(), operand=n.test)
        out.append(("negate condition", f))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        out.append(("drop not", None))           # handled by parent replacement
    if isinstance(node, ast.Constant):
        v = node.value
        if isinstance(v, bool):
            def f(n):
                n.value = not n.value
            out.append((f"const {v}->{not v}", f))
        elif isinstance(v, int) and not isinstance(v, bool):
            def f(n):
                n.value = n.value + 1
            out.append((f"const {v}->{v + 1}", f))
    if isinstance(node, ast.BinOp) and type(node.op) in SWAP_BIN:
        def f(n, _t=SWAP_BIN[type(node.op)]):
            n.op = _t()
        out.append((f"arith {type(node.op).__name__}->{SWAP_BIN[type(node.op)].__name__}", f))
    if isinstance(node, ast.Return) and node.value is not None:
        def f(n):
            n.value = ast.Constant(value=None)
        out.append(("return None", f))
    # String constants, docstrings excluded (changing one cannot alter behaviour,
    # so it would be an equivalent mutant manufactured on purpose).
    if (isinstance(node, ast.Constant) and isinstance(node.value, str)
            and node.value and id(node) not in _DOCSTRINGS):
        def f(n):
            n.value = "XX" + n.value + "XX"
        out.append(("string XX", f))
    # Statement deletion: the finest-grained reversion. Added after the first
    # task came back with ZERO sites - its whole fix was one assignment of a
    # call, which no comparison/boolean/arithmetic operator can touch. One-line
    # fixes are the common case, so an operator set without this measures the
    # operator set rather than the tests.
    if (isinstance(node, ast.stmt)
            and not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                                      ast.Pass, ast.Import, ast.ImportFrom))
            and not (isinstance(node, ast.Expr) and id(node.value) in _DOCSTRINGS)):
        out.append(("delete statement", "DELETE"))
    return [(name, fn) for name, fn in out if fn is not None]


_DOCSTRINGS: set[int] = set()


def _mark_docstrings(tree: ast.AST) -> None:
    _DOCSTRINGS.clear()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if (isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            _DOCSTRINGS.add(id(body[0].value))


def key(node) -> tuple:
    """Identity by location, not by traversal order - ast.walk is breadth-first
    and a transformer is depth-first, and matching by position across the two
    would mutate the wrong node without complaint."""
    return (type(node).__name__, node.lineno, node.col_offset,
            getattr(node, "end_lineno", None), getattr(node, "end_col_offset", None))


def sites(source: str, lines: set[int]) -> list[tuple[tuple, str]]:
    tree = ast.parse(source)
    _mark_docstrings(tree)
    found = []
    for node in ast.walk(tree):
        if getattr(node, "lineno", None) in lines:
            for name, _ in operators(node):
                found.append((key(node), name))
    return found


def mutate(source: str, k: tuple, name: str) -> str | None:
    tree = ast.parse(source)
    _mark_docstrings(tree)
    parents = {}
    for p in ast.walk(tree):
        for _, val in ast.iter_fields(p):
            if isinstance(val, list):
                for i, c in enumerate(val):
                    if isinstance(c, ast.AST):
                        parents[id(c)] = (val, i)
    for node in ast.walk(tree):
        if not hasattr(node, "lineno") or key(node) != k:
            continue
        for n, fn in operators(node):
            if n != name:
                continue
            if fn == "DELETE":
                if id(node) not in parents:
                    return None
                lst, i = parents[id(node)]
                lst[i] = ast.copy_location(ast.Pass(), node)
            else:
                fn(node)
            ast.fix_missing_locations(tree)
            try:
                return ast.unparse(tree)
            except Exception:                    # noqa: BLE001
                return None
    return None


# --- running the task's own suite ------------------------------------------

def suite(root: Path, env: dict, extra: list[str]) -> tuple[set[str], bool, int]:
    """Failing ids, whether it timed out, and the exit code. No shell."""
    cmd = [sys.executable, "-m", "pytest", "tests", "-q", "-rA",
           "-p", "no:cacheprovider", *extra]
    try:
        done = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return set(), True, -1
    out = (done.stdout or "") + (done.stderr or "")
    return {m.group(1) for m in FAILED.finditer(out)}, False, done.returncode


def changed_source(root: Path, base: str) -> dict[str, set[int]]:
    diff = subprocess.run(["git", "diff", "-U0", base], cwd=root, capture_output=True,
                          text=True, encoding="utf-8", errors="replace").stdout
    out, here = {}, None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            p = line[4:].strip()
            p = p[2:] if p.startswith("b/") else p
            here = p if p.endswith(".py") and not TEST_NAME.search(p) else None
        elif line.startswith("@@") and here:
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            start, count = int(m.group(1)), int(m.group(2) or 1)
            out.setdefault(here, set()).update(range(start, start + count))
    return {k: v for k, v in out.items() if v}


def one(task, fix: str, hold: Path) -> dict:
    root = hold / task.name
    root.mkdir(parents=True, exist_ok=True)
    base_tree(task, root)
    _seed_git(root)
    base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
                          text=True).stdout.strip()
    gold = subprocess.run(["git", "-C", task.source["repo"], "show", fix],
                          capture_output=True, timeout=180)
    applied = subprocess.run(["git", "-C", str(root), "apply", "--3way", "-"],
                             input=gold.stdout, capture_output=True, timeout=180)
    if applied.returncode != 0:
        return {"task": task.name, "why": "gold patch did not apply"}

    env = {**os.environ, **{k: str(v) for k, v in (task.source.get("env") or {}).items()}}

    red, timed, code = suite(root, env, [])
    if timed:
        return {"task": task.name, "why": "baseline suite timed out"}
    deselect = [a for rid in sorted(red) for a in ("--deselect", rid)]

    # Confirm the deselected baseline is green, or a "kill" means nothing.
    still, timed, code = suite(root, env, deselect)
    if still or code not in (0, 5):
        return {"task": task.name, "why": f"baseline not green after deselect ({len(still)} red, exit {code})"}

    changed = changed_source(root, base)
    if not changed:
        return {"task": task.name, "why": "gold patch changed no source lines"}

    # --- controls: the probe must be seen to flip, per task ----------------
    # Kill control: put the BASE version of every changed source file back.
    # That is stress.py's own reversion mutant, and the tests that the fix made
    # pass MUST now fail. If they do not, the suite is not reading this source
    # and every "survived" below would be an artifact.
    saved = {rel: (root / rel).read_text(encoding="utf-8") for rel in changed}
    for rel in changed:
        old = subprocess.run(["git", "show", f"{base}:{rel}"], cwd=root,
                             capture_output=True, text=True, encoding="utf-8")
        if old.returncode == 0:
            (root / rel).write_text(old.stdout, encoding="utf-8")
    try:
        failing, timed, code = suite(root, env, deselect + ["-x"])
    finally:
        for rel, body in saved.items():
            (root / rel).write_text(body, encoding="utf-8")
    kill_ok = timed or bool(failing) or code not in (0, 5)

    # Survive control: a statement that cannot change behaviour. If THIS is
    # "killed", the suite is flaky or the harness over-reports kills.
    first = sorted(changed)[0]
    body = saved[first]
    (root / first).write_text(body + "\n_ep_probe_noop = 0\n", encoding="utf-8")
    try:
        failing, timed, code = suite(root, env, deselect + ["-x"])
    finally:
        (root / first).write_text(body, encoding="utf-8")
    survive_ok = not timed and not failing and code in (0, 5)

    if not (kill_ok and survive_ok):
        return {"task": task.name, "why": f"CONTROL FAILED kill_ok={kill_ok} "
                                          f"survive_ok={survive_ok} - harness result, not a finding"}

    candidates = []
    for rel, lines in sorted(changed.items()):
        src = (root / rel).read_text(encoding="utf-8")
        for pos, name in sites(src, lines):
            candidates.append((rel, pos, name))
    if not candidates:
        return {"task": task.name, "changed": {k: len(v) for k, v in changed.items()},
                "sites": 0, "mutants": []}

    # Deterministic, spread across the whole set rather than the first few.
    step = max(1, len(candidates) // MAX_MUTANTS)
    chosen = candidates[::step][:MAX_MUTANTS]

    results = []
    for rel, pos, name in chosen:
        path = root / rel
        original = path.read_text(encoding="utf-8")
        mutated = mutate(original, pos, name)
        if mutated is None or mutated == ast.unparse(ast.parse(original)):
            results.append({"file": rel, "op": name, "verdict": "not generated"})
            continue
        path.write_text(mutated, encoding="utf-8")
        try:
            failing, timed, code = suite(root, env, deselect + ["-x"])
        finally:
            path.write_text(original, encoding="utf-8")
        if timed:
            verdict = "killed (timeout)"
        elif failing or code not in (0, 5):
            verdict = "killed"
        else:
            verdict = "SURVIVED"
        results.append({"file": rel, "op": name, "verdict": verdict,
                        "diff": _show(original, mutated)})
    return {"task": task.name, "baseline_red": len(red),
            "changed": {k: len(v) for k, v in changed.items()},
            "sites": len(candidates), "mutants": results}


def _show(a: str, b: str) -> str:
    """The one line that differs, for a human to judge equivalence."""
    x = ast.unparse(ast.parse(a)).splitlines()
    y = b.splitlines()
    for i, (p, q) in enumerate(zip(x, y)):
        if p != q:
            return f"{p.strip()[:70]}  ->  {q.strip()[:70]}"
    return ""


def main():
    want = sys.argv[1:] or None
    rows = {r["name"]: r for r in json.loads(CORPUS.read_text(encoding="utf-8"))}
    tasks = [t for t in load_mined() if t.name in rows and (not want or t.name in want)]
    report = []
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="ep-mutant-", ignore_cleanup_errors=True) as tmp:
        for task in tasks:
            t0 = time.time()
            try:
                r = one(task, rows[task.name]["fix"], Path(tmp))
            except Exception as e:                 # noqa: BLE001
                r = {"task": task.name, "why": f"{type(e).__name__}: {e}"}
            r["seconds"] = round(time.time() - t0)
            report.append(r)
            ms = r.get("mutants", [])
            live = sum(1 for m in ms if m["verdict"] == "SURVIVED")
            made = sum(1 for m in ms if m["verdict"] != "not generated")
            said = r.get("why") or f"{live}/{made} survived  sites={r.get('sites')}"
            print(f"{task.name:24s} {said}  ({r['seconds']}s)", flush=True)
    Path(__file__).with_name("mutants.json").write_text(
        json.dumps(report, indent=1), encoding="utf-8")
    print(f"\ntotal {round(time.time() - started)}s")


if __name__ == "__main__":
    main()
