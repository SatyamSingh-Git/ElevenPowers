"""Build tasks from somebody else's real bug fixes.

Every task suite written for this project has been written by the person whose
code it grades, and the population problem has bitten five times: hook payloads,
gate scenarios, claim prompts, and two rounds of seeded bugs each agreed with the
assumptions of the code they were meant to test.

SWE-bench solves this by taking real pull requests and splitting their tests into
FAIL_TO_PASS, which must go from red to green, and PASS_TO_PASS, which must stay
green. Its harness needs Docker. The construction does not: a git repository, a
commit that changes source and tests together, and a test runner are enough.

    python -m eval.mine --repo DIR --out FILE [--limit 60] [--want 8]

For each candidate commit the procedure is SWE-bench's own:

1. check out the parent, which is the code the agent will be given
2. write in only the test files as the fix commit left them
3. run those tests: the ones that fail are the fail-to-pass set, and a commit
   with none is discarded because nothing about it can be verified
4. check out the fix and run the same tests: they must now pass, or the commit
   did not do what its tests claim
5. run the existing suite at the parent: it must be green, or the agent starts
   from a broken repository and a green run proves nothing

Only commits surviving all five become tasks. Everything about them, the code,
the bug, the tests and the wording of the report, was written by someone with no
knowledge of this project.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

NODE = re.compile(r"^(?P<node>\S+::\S+)\s+(?:FAILED|ERROR)|^(?:FAILED|ERROR)\s+(?P<alt>\S+::\S+)",
                  re.MULTILINE)
# Generous for a suite that runs in seconds, short enough that one hanging
# commit costs a couple of minutes rather than derailing the run.
TIMEOUT = 120


@dataclass
class Instance:
    name: str
    repo: str
    base: str
    fix: str
    prompt: str
    hidden_files: dict[str, str] = field(default_factory=dict)
    f2p: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    changed: list[str] = field(default_factory=list)


def git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, timeout=TIMEOUT)
    return done.stdout if done.returncode == 0 else ""


def materialise(repo: Path, sha: str, into: Path) -> None:
    """The repository as it stood at `sha`, without its history.

    A zip through git archive rather than a worktree or a tar pipe, because it
    is the one form that behaves the same on every platform.
    """
    into.mkdir(parents=True, exist_ok=True)
    bundle = into.parent / f"{sha[:12]}.zip"
    subprocess.run(["git", "-C", str(repo), "archive", "--format=zip", "-o",
                    str(bundle), sha], check=True, capture_output=True, timeout=TIMEOUT)
    with zipfile.ZipFile(bundle) as archive:
        archive.extractall(into)
    bundle.unlink(missing_ok=True)


def run_tests(root: Path, targets: list[str], env: dict[str, str]) -> tuple[int, str]:
    import os

    environment = {**os.environ, **env}
    done = subprocess.run(
        [sys.executable, "-m", "pytest", *targets, "-q", "--no-header", "-p", "no:randomly"],
        cwd=root, capture_output=True, text=True, timeout=TIMEOUT, env=environment,
    )
    return done.returncode, (done.stdout or "") + (done.stderr or "")


def failing_nodes(output: str) -> list[str]:
    found = []
    for match in NODE.finditer(output):
        node = match.group("node") or match.group("alt")
        if node and node not in found:
            found.append(node)
    return found


# A revert's message is not a bug report: it says "this reverts commit <sha>"
# and names something the agent cannot see. A re-land is the same change as the
# commit it restores, and counting both would count one bug twice in a paired
# comparison. Both are what SWE-bench's human validation pass exists to catch.
REVERT = re.compile(r"^\s*revert\b", re.I)


def usable_report(subject: str, seen: set[str]) -> bool:
    if REVERT.match(subject):
        return False
    return subject.strip().lower() not in seen


def candidates(repo: Path, limit: int, source_dir: str, test_dir: str) -> list[tuple[str, list[str]]]:
    """Commits that changed source and tests together, newest first.

    A fix without a test cannot be verified, and a test without a fix is not a
    bug report. Merges are skipped because their diff is not one change.
    """
    log = git(repo, "log", "--no-merges", "--format=%H", f"-{limit}")
    out, seen = [], set()
    for sha in log.split():
        subject = git(repo, "log", "-1", "--format=%s", sha).strip()
        if not usable_report(subject, seen):
            continue
        files = git(repo, "show", "--name-only", "--format=", sha).split()
        touched_source = [f for f in files if f.startswith(source_dir)]
        touched_tests = [f for f in files if f.startswith(test_dir) and f.endswith(".py")]
        if touched_source and touched_tests:
            seen.add(subject.lower())
            out.append((sha, touched_tests))
    return out


def describe(repo: Path, sha: str) -> str:
    """The bug report, which is the commit message as its author wrote it."""
    body = git(repo, "log", "-1", "--format=%s%n%n%b", sha).strip()
    lines = [ln for ln in body.splitlines() if not ln.startswith("Co-authored-by")]
    return "\n".join(lines).strip()[:1200]


def validate(repo: Path, sha: str, test_files: list[str], env: dict[str, str],
             work: Path) -> Instance | None:
    parent = git(repo, "rev-parse", f"{sha}^").strip()
    if not parent:
        return None

    fixed = work / "fixed"
    materialise(repo, sha, fixed)
    patch = {}
    for rel in test_files:
        path = fixed / rel
        if path.exists():
            patch[rel] = path.read_text(encoding="utf-8", errors="ignore")
    if not patch:
        return None

    base = work / "base"
    materialise(repo, parent, base)

    # The suite as the agent will find it has to be green, or a green run proves
    # nothing and the task cannot distinguish a fix from a repository that was
    # already broken.
    code, _ = run_tests(base, [d for d in ("tests",) if (base / d).exists()], env)
    if code != 0:
        return None

    for rel, body in patch.items():
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")

    code, output = run_tests(base, list(patch), env)
    if code == 0:
        return None                      # nothing fails, so nothing is proved
    f2p = failing_nodes(output)
    if not f2p:
        return None

    code, output = run_tests(fixed, f2p, env)
    if code != 0:
        return None                      # the fix does not satisfy its own tests

    return Instance(
        name=f"{repo.name}-{sha[:8]}", repo=str(repo), base=parent, fix=sha,
        prompt=describe(repo, sha), hidden_files=patch, f2p=f2p, env=env,
        changed=[f for f in git(repo, "show", "--name-only", "--format=", sha).split()
                 if f.endswith(".py")],
    )


def mine(repo: Path, limit: int, want: int, env: dict[str, str],
         source_dir: str, test_dir: str) -> list[Instance]:
    found: list[Instance] = []
    pool = candidates(repo, limit, source_dir, test_dir)
    print(f"{len(pool)} commits changed source and tests together, of the last {limit}")
    for sha, tests in pool:
        if len(found) >= want:
            break
        # Windows holds file handles open a moment after pytest exits, so a
        # strict cleanup takes the whole run down on somebody else's temp file.
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            try:
                instance = validate(repo, sha, tests, env, Path(tmp))
            except (subprocess.SubprocessError, OSError, zipfile.BadZipFile) as exc:
                print(f"  {sha[:8]}  skipped: {type(exc).__name__}", flush=True)
                continue
        mark = f"kept, {len(instance.f2p)} failing test(s)" if instance else "no usable transition"
        print(f"  {sha[:8]}  {mark}", flush=True)
        if instance:
            found.append(instance)
    return found


def main(argv: list[str]) -> int:
    def option(flag, default):
        return argv[argv.index(flag) + 1] if flag in argv else default

    repo = Path(option("--repo", ""))
    if not repo.exists():
        print(__doc__)
        return 1
    env = {"PYTHONPATH": option("--pythonpath", "src")}
    found = mine(repo, int(option("--limit", "60")), int(option("--want", "8")), env,
                 option("--source-dir", "src"), option("--test-dir", "tests"))

    out = Path(option("--out", "mined.json"))
    out.write_text(json.dumps([i.__dict__ for i in found], indent=1), encoding="utf-8")
    print(f"\n{len(found)} validated instance(s) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
