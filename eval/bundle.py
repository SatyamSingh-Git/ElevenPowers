"""A run, preserved well enough to be graded again by someone who was not there.

Twelve candidate patches were deleted with their `TemporaryDirectory`. When the
grader turned out to be blind to regressions, there was nothing left to
re-grade, so a published null became permanently unrecheckable rather than
merely wrong. That is the cost this module exists to stop repeating.

A bundle holds what a second opinion needs: which task, at which base commit,
under which arm and which resolved model; the candidate as a patch; what the
host reported; what the runtime recorded; and what the grader concluded, with
the node outcomes it concluded it from.

The patch matters more than the workspace. A workspace is a machine's worth of
state that only reproduces on that machine; a patch plus a base identity
reconstructs the candidate anywhere, which is the point of keeping it.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


# Not part of anybody's answer: compiled bytecode, test-runner caches, the
# host's own settings, and the runtime's ledger. Staged by `git add -A` in a
# workspace with no ignore rules of its own, they made the exported candidate
# mostly `.pyc` blobs — and `git apply` rejects the whole patch over them.
# Excluding the ledger matters for a second reason: it is written only under the
# gated arms, so leaving it in would make those patches differ from the plain
# ones for a reason that has nothing to do with the code.
ARTEFACTS = (
    "__pycache__/", "*.pyc", "*.pyo", ".pytest_cache/", ".mypy_cache/",
    ".ruff_cache/", ".elevenpowers/", ".claude/", "*.egg-info/",
)


def ignore_artefacts(root: Path) -> None:
    """Keep workspace noise out of the candidate, without touching the tree.

    `.git/info/exclude` rather than a `.gitignore`: it is per-repository and
    untracked, so the agent never sees it, it does not alter the base the task
    presents, and it cannot collide with an ignore file a mined repository
    already ships.
    """
    info = root / ".git" / "info"
    info.mkdir(parents=True, exist_ok=True)
    (info / "exclude").write_text("\n".join(ARTEFACTS) + "\n", encoding="utf-8")


def seed_commit(root: Path) -> str:
    """The commit the workspace was built at, before the agent touched it."""
    done = subprocess.run(["git", "-C", str(root), "rev-list", "--max-parents=0", "HEAD"],
                          capture_output=True, text=True)
    return done.stdout.split()[0] if done.returncode == 0 and done.stdout.split() else ""


def export_patch(root: Path) -> str:
    """Everything the agent changed, as a patch against the seeded base.

    Staged first, so files it created are in the diff; against the root commit
    rather than HEAD, because an agent that committed its own work would
    otherwise export nothing at all.
    """
    base = seed_commit(root)
    if not base:
        return ""
    subprocess.run(["git", "-C", str(root), "add", "-A"], capture_output=True)
    done = subprocess.run(["git", "-C", str(root), "diff", "--binary", base],
                          capture_output=True, text=True)
    return done.stdout if done.returncode == 0 else ""


def apply_patch(root: Path, patch: str) -> str:
    """Empty on success, git's complaint otherwise.

    A grader that reports "the patch did not apply" and not why sends whoever
    reads it back to a workspace that no longer exists, which is the failure
    this module is here to prevent.
    """
    if not patch.strip():
        return ""
    # `git apply` resolves paths against the enclosing repository rather than
    # the working directory, and when the two differ it skips every file and
    # still exits zero. A home directory under version control is enough to
    # trigger that, and the symptom is a grade computed against the base tree
    # with nothing anywhere reporting a problem. Giving the workspace its own
    # repository makes the working directory the top level.
    if not (root / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=root, capture_output=True)
    done = subprocess.run(["git", "apply", "--verbose", "--whitespace=nowarn", "-"],
                          cwd=root, input=patch, capture_output=True, text=True)
    if done.returncode != 0:
        return (done.stderr or "git apply failed").strip()
    # Belt and braces against the same class: a zero exit is not the claim.
    skipped = [ln for ln in done.stderr.splitlines() if "Skipped patch" in ln]
    return "; ".join(skipped)


def write(into: Path, *, task: str, arm: str, model: str, asked: str, patch: str,
          answer: dict, limits: dict, ledger: Path | None,
          source: dict | None, environment: dict | None = None,
          blindspots: Path | None = None) -> Path:
    """One directory per run, named so a person can find it.

    Both models are recorded: `model` is what the host resolved and `asked` is
    the alias requested. An alias can point somewhere else between two runs, and
    a comparison that keeps only the alias could never say so.
    """
    into.mkdir(parents=True, exist_ok=True)
    (into / "manifest.json").write_text(json.dumps({
        "task": task,
        "arm": arm,
        "model": model,
        "model_asked": asked,
        "base": {k: source.get(k) for k in ("repo", "base")} if source else None,
        "required": {"f2p": (source or {}).get("f2p", []),
                     "p2p": (source or {}).get("p2p", [])},
        # What the maintainer changed, so a reader of this bundle alone can ask
        # whether the candidate found the right files. A bundle that needs the
        # corpus to be interpretable is not the self-contained thing E3 bought.
        "gold": (source or {}).get("changed", []),
        "gold_lines": (source or {}).get("gold_lines", 0),
        "env": (source or {}).get("env", {}),
        "limits": limits,
        "environment": environment or {},
    }, indent=1), encoding="utf-8")
    (into / "patch.diff").write_text(patch, encoding="utf-8")
    (into / "answer.json").write_text(json.dumps(answer, indent=1), encoding="utf-8")
    if ledger and ledger.exists():
        (into / "ledger.json").write_text(ledger.read_text(encoding="utf-8"), encoding="utf-8")
    if blindspots and blindspots.exists():
        (into / "blindspots.jsonl").write_text(blindspots.read_text(encoding="utf-8"),
                                               encoding="utf-8")
    return into


def record_grade(into: Path, graded) -> None:
    """What the grader concluded, and the node outcomes behind it.

    Both, because a stored verdict nobody can check is the same problem one
    level up: the reason this module exists is that a verdict outlived its
    evidence.
    """
    (into / "grade.json").write_text(json.dumps({
        "resolved": graded.resolved,
        "outcome": graded.outcome,
        "detail": graded.detail,
        "passed": list(graded.observed),
    }, indent=1), encoding="utf-8")


def read(directory: Path) -> dict:
    out = {}
    for name in ("manifest", "answer", "grade"):
        path = directory / f"{name}.json"
        if path.exists():
            out[name] = json.loads(path.read_text(encoding="utf-8"))
    patch = directory / "patch.diff"
    out["patch"] = patch.read_text(encoding="utf-8") if patch.exists() else ""
    return out
