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

from .live import grade_patch
from .task import Task

BUGGY = "def double(n):\n    return n\n\n\ndef label():\n    return 'ok'\n"
FIXED = "def double(n):\n    return n * 2\n\n\ndef label():\n    return 'ok'\n"
KEEP = "from src.app import label\n\n\ndef test_label():\n    assert label() == 'ok'\n"
NEW = "from src.app import double\n\n\ndef test_double():\n    assert double(2) == 4\n"


def _git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), *args], check=True,
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
        (repo / rel).write_text(body, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    base = _commit(repo, "the code before the fix")

    (repo / "src/app.py").write_text(FIXED, encoding="utf-8")
    (repo / "tests/test_new.py").write_text(NEW, encoding="utf-8")
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


def main(argv: list[str]) -> int:
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
