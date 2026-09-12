"""Does the grader give the right answer to a question with a known answer?

    python -m eval.validate

Every measurement this project has published came out of a grader nobody had
graded. That grader ran only the tests a patch was supposed to make pass, so
"resolved" meant the requested behaviour works and not "and nothing else broke",
and the twelve-bug null was measured with it. The defect was found by reading
the code rather than by running it, because nothing ran it against a case whose
answer was already known.

So: four patches with four known answers, built from a real two-commit repository
mined the way `eval.mine` mines one.

`--corpus` asks the same question of every mined task, using the maintainer's own
fix as the patch. It exists because a pre-flight that sampled two tasks out of
fifteen passed while the grader was corrupting every patch it was handed: both
samples happened to survive it, and outcome is exactly the observable luck can
supply. Fifteen tasks, two questions each, and it costs nothing but CPU.

| patch | must come out as |
|---|---|
| the maintainer's own fix | `resolved` |
| the fix, plus a break elsewhere | `regressed` |
| a patch that changes nothing relevant | `unfixed` |
| a workspace the evaluator cannot build | `setup` |

The third and fourth matter as much as the first two. A grader that answers
`resolved` to everything passes the first row; one that answers `regressed` to
everything passes the second; and a run that fails because the harness broke must
not be counted against the agent.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from .bundle import GIT
from .live import grade_patch
from .task import Task

BUGGY = "def double(n):\n    return n\n\n\ndef label():\n    return 'ok'\n"
FIXED = "def double(n):\n    return n * 2\n\n\ndef label():\n    return 'ok'\n"
KEEP = "from src.app import label\n\n\ndef test_label():\n    assert label() == 'ok'\n"
NEW = "from src.app import double\n\n\ndef test_double():\n    assert double(2) == 4\n"


def _git(repo: Path, *args: str) -> str:
    done = subprocess.run([*GIT, "-C", str(repo), *args], check=True,
                          capture_output=True, text=True)
    return done.stdout.strip()


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=E", "-c", "user.email=e@example.invalid",
         "commit", "-qm", message)
    return _git(repo, "rev-parse", "HEAD")


def fixture(into: Path) -> Task:
    """A repository with a bug at one commit and its fix at the next."""
    repo = into / "upstream"
    (repo / "src").mkdir(parents=True)
    (repo / "tests").mkdir()
    for rel, body in ((".gitignore", "__pycache__/\n"), ("src/__init__.py", ""),
                      ("src/app.py", BUGGY), ("tests/__init__.py", ""),
                      ("tests/test_keep.py", KEEP)):
        # Bytes: the patches below are built from these constants, so the file
        # on disk has to be the constant and not the platform's idea of it.
        (repo / rel).write_bytes(body.encode("utf-8"))
    subprocess.run([*GIT, "init", "-q"], cwd=repo, check=True, capture_output=True)
    base = _commit(repo, "the code before the fix")

    (repo / "src/app.py").write_bytes(FIXED.encode("utf-8"))
    (repo / "tests/test_new.py").write_bytes(NEW.encode("utf-8"))
    _commit(repo, "double() returned its argument unchanged")

    return Task(
        name="validate", prompt="double is wrong", files={}, hidden="",
        why="the grader is being graded",
        source={"repo": str(repo), "base": base, "env": {},
                "hidden_files": {"tests/test_new.py": NEW},
                "f2p": ["tests/test_new.py::test_double"],
                "p2p": ["tests/test_keep.py::test_label"]},
    )


def _patch(before: str, after: str, path: str = "src/app.py") -> str:
    body = "".join(
        f"-{line}\n" for line in before.splitlines()
    ) + "".join(f"+{line}\n" for line in after.splitlines())
    return (f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n"
            f"@@ -1,{len(before.splitlines())} +1,{len(after.splitlines())} @@\n{body}")


CASES = [
    ("the maintainer's own fix", lambda: _patch(BUGGY, FIXED), "resolved"),
    ("the fix, and a break elsewhere",
     lambda: _patch(BUGGY, FIXED.replace("'ok'", "'broken'")), "regressed"),
    ("a patch that changes nothing relevant",
     lambda: _patch(BUGGY, BUGGY.replace("def label", "def label  ")), "unfixed"),
    ("a workspace that cannot be built", lambda: "not a patch at all\n", "setup"),
]


def gold_patch(task: Task, fix: str) -> str:
    """The maintainer's own change, minus the tests the grader restores itself."""
    source = [p for p in task.source["changed"] if not p.startswith("tests/")]
    done = subprocess.run([*GIT, "-C", task.source["repo"], "diff",
                           task.source["base"], fix, "--", *source],
                          capture_output=True)
    return done.stdout.decode("utf-8")


def over_corpus(lock: Path) -> int:
    """Every mined task, asked whether it can tell a fix from no fix at all.

    A task where the empty patch already resolves is not measuring anything: its
    required test passes at the base commit. A task where the maintainer's own
    fix does not resolve is mined wrong, or its environment is missing. Neither
    can be seen from a score, and both are invisible in a sample of two.
    """
    import json

    from .mined import load as load_mined

    fixes = {r["name"]: r["fix"] for r in
             json.loads(lock.read_text(encoding="utf-8"))}
    tasks = load_mined()
    if not tasks:
        print("no mined tasks. Set EP_MINED to a corpus built by python -m eval.corpus")
        return 1

    print(f"{'task':<26}{'gold':<12}{'empty':<12}  nodes")
    wrong = []
    for task in tasks:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            into = Path(tmp)
            gold = grade_patch(task, gold_patch(task, fixes[task.name]), into / "gold")
            empty = grade_patch(task, "", into / "empty")
        bad = gold.outcome != "resolved" or empty.outcome != "unfixed"
        wrong.append((task.name, gold, empty)) if bad else None
        print(f"{task.name:<26}{gold.outcome:<12}{empty.outcome:<12}"
              f"{len(gold.observed):>6}{'   <-- WRONG' if bad else ''}", flush=True)

    print()
    for name, gold, empty in wrong:
        print(f"{name}: gold {gold.outcome} ({(gold.detail or '')[:80]}), "
              f"empty {empty.outcome}")
    if wrong:
        print()
        print(f"{len(wrong)} of {len(tasks)} tasks cannot tell a fix from no fix.")
        return 1
    print(f"all {len(tasks)} tasks: the maintainer's fix resolves and the empty "
          "patch does not.")
    return 0


def main(argv: list[str]) -> int:
    if "--corpus" in argv:
        where = argv.index("--corpus") + 1
        lock = Path(argv[where] if where < len(argv) else "eval/corpus.lock")
        return over_corpus(lock)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        into = Path(tmp)
        task = fixture(into)
        print(f"{'case':<40}{'expected':<12}{'got':<12}")
        wrong = 0
        for n, (name, make, expected) in enumerate(CASES):
            got = grade_patch(task, make(), into / f"court{n}")
            mark = "" if got.outcome == expected else "   <-- WRONG"
            wrong += mark != ""
            print(f"{name:<40}{expected:<12}{got.outcome:<12}{mark}")

    print()
    if wrong:
        print(f"{wrong} of {len(CASES)} cases came out wrong. The grader is not usable.")
        return 1
    print(f"all {len(CASES)} cases correct: the grader separates a fix from a")
    print("regression, from a patch that did nothing, and from its own breakage.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
