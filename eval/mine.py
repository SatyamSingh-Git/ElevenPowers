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
6. run the whole suite at both ends and keep what passes at both: that is the
   pass-to-preserve set, and a commit without one is discarded because a task
   that cannot show a regression cannot grade a fix

Only commits surviving all six become tasks. Everything about them, the code,
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

from .bundle import GIT
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
    origin: str
    """Where the repository came from, so the instance is not tied to one disk.

    `repo` is a path on the machine that mined it. On its own that makes an
    instance unreconstructible anywhere else, which is the same defect as
    keeping a verdict without its evidence — recorded here rather than
    rediscovered later.
    """
    base: str
    fix: str
    prompt: str
    hidden_files: dict[str, str] = field(default_factory=dict)
    f2p: list[str] = field(default_factory=list)
    p2p: list[str] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)
    """Nodes excluded from the preservation set for naming the machine.

    click parametrises a test on `importlib.metadata.version("click")`, so the
    installed version lands inside the node id and the next machine collects a
    differently named node. Keeping it would report an absence as a regression;
    dropping it silently would be a preservation set that quietly shrank. It is
    one node out of eighteen hundred, and it is written down.
    """
    env: dict[str, str] = field(default_factory=dict)
    changed: list[str] = field(default_factory=list)
    gold_files: int = 0
    gold_lines: int = 0
    """How large the maintainer's own source change was.

    Recorded so difficulty can be a **label** rather than a filter. The rule
    this project used before — keep a task only if the naive fix breaks the
    visible suite — selected the benchmark around the mechanism being measured,
    which is audit finding E6. A measured property of the gold patch says
    something about the task without deciding which tasks are allowed to exist.
    """


def git(repo: Path, *args: str) -> str:
    """Always a string, decoded as utf-8 rather than the machine's codepage.

    A commit subject in click's history carries a byte cp1252 has no character
    for, and the default decode raised inside subprocess's reader thread: the
    call returned None, and mining crashed on `.strip()` several frames away.
    Scanning deeper history was the only thing that reached it, so the corpus
    had a depth limit nobody had chosen.
    """
    done = subprocess.run([*GIT, "-C", str(repo), *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT)
    return (done.stdout or "") if done.returncode == 0 else ""


def materialise(repo: Path, sha: str, into: Path) -> None:
    """The repository as it stood at `sha`, without its history.

    A zip through git archive rather than a worktree or a tar pipe, because it
    is the one form that behaves the same on every platform.
    """
    into.mkdir(parents=True, exist_ok=True)
    bundle = into.parent / f"{sha[:12]}.zip"
    subprocess.run([*GIT, "-C", str(repo), "archive", "--format=zip", "-o",
                    str(bundle), sha], check=True, capture_output=True, timeout=TIMEOUT)
    with zipfile.ZipFile(bundle) as archive:
        archive.extractall(into)
    bundle.unlink(missing_ok=True)


def run_tests(root: Path, targets: list[str], env: dict[str, str],
              traceback: str = "no") -> tuple[int, str]:
    """Run a suite and return its exit code with everything it said.

    `traceback` defaults to none because the callers that parse node ids do not
    want it. The one caller that needs a *reason* asks for it: with `--tb=no` a
    collection failure prints "2 errors during collection" and nothing else, so
    the missing module's name — the only actionable part — is thrown away before
    anyone can read it.
    """
    import os

    environment = {**os.environ, **env}
    done = subprocess.run(
        [sys.executable, "-m", "pytest", *targets, "-q", "--no-header",
         f"--tb={traceback}", "-rA", "-p", "no:randomly"],
        cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT, env=environment,
    )
    return done.returncode, (done.stdout or "") + (done.stderr or "")


def failing_nodes(output: str) -> list[str]:
    found = []
    for match in NODE.finditer(output):
        node = match.group("node") or match.group("alt")
        if node and node not in found:
            found.append(node)
    return found


def passing_nodes(output: str) -> set[str]:
    """Which tests actually ran and passed, from `-rA`'s summary.

    An exit code says the run was green; it does not say the tests anyone cared
    about were collected at all. Grading needs the second thing.
    """
    return {line.split()[1] for line in output.splitlines()
            if line.startswith("PASSED ") and "::" in line}


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
    # One `git log`, not two subprocesses per commit. At the depth needed to
    # find enough instances that is twenty thousand process spawns, which on
    # Windows is most of an hour spent on nothing -- and it was the reason the
    # corpus had never been mined deeper than a couple of hundred commits.
    log = git(repo, "log", "--no-merges", "--name-only",
              "--format=%x1e%H%x1f%s", f"-{limit}")
    out, seen = [], set()
    for chunk in log.split("\x1e")[1:]:
        header, _, listing = chunk.partition("\n")
        sha, _, subject = header.partition("\x1f")
        subject = subject.strip()
        if not usable_report(subject, seen):
            continue
        files = listing.split()
        touched_source = [f for f in files if f.startswith(source_dir)]
        touched_tests = [f for f in files if f.startswith(test_dir) and f.endswith(".py")]
        if touched_source and touched_tests:
            seen.add(subject.lower())
            out.append((sha, touched_tests))
    return out


def origin(repo: Path) -> str:
    return git(repo, "config", "--get", "remote.origin.url").strip()


def changed_lines(repo: Path, sha: str, paths: list[str]) -> int:
    """Lines the maintainer changed in source, tests excluded.

    The test files are the answer key; counting them would make a task look
    large because its author wrote thorough tests, which says nothing about the
    change an agent has to find.
    """
    if not paths:
        return 0
    stat = git(repo, "show", "--numstat", "--format=", sha)
    total = 0
    for line in stat.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[2] in paths and parts[0].isdigit() and parts[1].isdigit():
            total += int(parts[0]) + int(parts[1])
    return total


ASK = """Make this change to the repository in the current directory.

What follows is the message from the commit that made it upstream, written
after the fact by its author. The change itself has not been made here: the
code in front of you is the state before it.

"""


def describe(repo: Path, sha: str) -> str:
    """The commit message, framed as a request rather than pasted as one.

    A commit message describes work already done, and handed over bare it does
    not read as a task. Measured across ninety runs, ten percent ended within
    three turns with the agent replying that this looks like a pasted PR title
    and asking what it was meant to do -- a fair reading, and nothing to do
    with whether it can fix bugs. Every one was recorded as a task it failed.

    The wrapper is identical for every instance, so it cannot favour an arm,
    and it adds nothing about the fix the message did not already carry. That
    matters more than the wasted money: the gate works by refusing to let an
    agent stop, so on an ambiguous prompt it would show a gain for talking the
    agent out of asking a reasonable question, which is not the claim at issue.
    """
    body = git(repo, "log", "-1", "--format=%s%n%n%b", sha).strip()
    lines = [ln for ln in body.splitlines() if not ln.startswith("Co-authored-by")]
    return ASK + "\n".join(lines).strip()[:1200]


def validate(repo: Path, sha: str, test_files: list[str], env: dict[str, str],
             work: Path) -> tuple[Instance | None, str]:
    """A usable instance, or the reason there is not one.

    The reason matters as much as the instance. Five different rejections used
    to return a bare `None`, so a repository that yielded nothing because its
    test dependencies were missing looked exactly like one with no bugs in it —
    and the caller printed neither. A corpus that quietly cannot be built is the
    same failure as a check that quietly does nothing.
    """
    parent = git(repo, "rev-parse", f"{sha}^").strip()
    if not parent:
        return None, "no parent commit"

    fixed = work / "fixed"
    materialise(repo, sha, fixed)
    patch = {}
    for rel in test_files:
        path = fixed / rel
        if path.exists():
            patch[rel] = path.read_text(encoding="utf-8", errors="ignore")
    if not patch:
        return None, "the commit's test files are not in its tree"

    base = work / "base"
    materialise(repo, parent, base)
    suite = [d for d in ("tests",) if (base / d).exists()]

    for rel, body in patch.items():
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")

    # The cheap questions first. Running the whole suite before them costs a
    # full test run on every candidate, and on markupsafe eight of nine are
    # rejected by checks that only ever needed the commit's own test files. The
    # set of instances kept is unchanged -- these are all conjuncts -- but the
    # depth of history that can be searched in an afternoon is not.
    code, output = run_tests(base, list(patch), env, traceback="line")
    if code == 0:
        return None, "the new tests already pass before the fix"
    f2p = failing_nodes(output)
    if not f2p:
        # A suite that cannot import its dependencies also exits non-zero with
        # nothing named, and reporting that as "no node id" is how a repository
        # with a missing package looked like a repository with no bugs.
        return None, _why_red(output)

    code, output = run_tests(fixed, f2p, env)
    if code != 0:
        return None, "the fix does not satisfy its own tests"

    # The suite as the agent will find it has to be green, or a green run proves
    # nothing and the task cannot distinguish a fix from a repository that was
    # already broken. Asked of survivors only.
    green = work / "green"
    materialise(repo, parent, green)
    code, output = run_tests(green, suite, env, traceback="line")
    if code != 0:
        return None, _why_red(output)

    # The preservation set: what is green with the fix commit's tests in place,
    # both before and after the source change. A task without one cannot tell a
    # fix from a patch that also broke something, which is how the grader came
    # to accept exactly that.
    _, before = run_tests(base, suite, env)
    _, after = run_tests(fixed, suite, env)
    p2p = sorted((passing_nodes(before) & passing_nodes(after)) - set(f2p))
    if machine_dependent(f2p):
        # The required test itself. There is nothing to fall back on: the task
        # asks for a node whose name the next machine will not produce.
        return None, f"machine-dependent required node: {machine_dependent(f2p)[0]}"
    dropped = machine_dependent(p2p)
    p2p = [n for n in p2p if n not in set(dropped)]
    if not p2p:
        return None, "nothing to preserve, so a regression could not be seen"

    changed = [f for f in git(repo, "show", "--name-only", "--format=", sha).split()
               if f.endswith(".py")]
    source_only = [f for f in changed if f not in patch]
    return Instance(
        name=f"{repo.name}-{sha[:8]}", repo=str(repo), origin=origin(repo),
        base=parent, fix=sha, prompt=describe(repo, sha), hidden_files=patch,
        f2p=f2p, p2p=p2p, dropped=dropped, env=env, changed=changed,
        gold_files=len(source_only), gold_lines=changed_lines(repo, sha, source_only),
    ), "kept"


def machine_dependent(nodes: list[str]) -> list[str]:
    """Node ids that name an installed distribution and its version.

    A pinned identifier containing a value read from the machine is not pinned.
    click's `test_attr_deprecated` parametrises on
    `importlib.metadata.version("click")`, so the version lands inside the id,
    and the corpus pinned `...[click-__version__-8.4.2.dev0]` into four
    preservation sets. That version is click's at none of those commits: it is
    what setuptools-scm falls back to inside a tree with no git history, which
    is what a stray `pip install -e .` saw. Install click properly and the node
    is renamed, never collected, and reported as a regression that is really an
    absence.

    Both halves are required -- the distribution's name *and* its version -- so
    that an ordinary parameter that happens to look like a version is left
    alone. This catches the class that has actually bitten, not every way an id
    can be unstable.
    """
    import importlib.metadata

    installed = []
    for dist in importlib.metadata.distributions():
        name = (dist.metadata["Name"] or "").strip()
        version = (dist.version or "").strip()
        if name and version:
            installed.append((name.lower(), version))
    out = []
    for node in nodes:
        _, _, params = node.partition("[")
        if not params:
            continue
        low = params.lower()
        if any(name in low and version in params for name, version in installed):
            out.append(node)
    return out


def _why_red(output: str) -> str:
    """Separate a repository that cannot be set up from one that is broken.

    A missing test dependency is an environment problem and is fixable by
    installing it; a genuinely failing suite at the base commit is a property of
    the repository. Reporting both as "rejected" is how three of five
    repositories contributed nothing without anyone being told.
    """
    missing = sorted(set(re.findall(r"No module named '([^']+)'", output)))
    if missing:
        return f"setup: missing dependency {', '.join(missing)}"
    if "errors during collection" in output:
        return "setup: the test suite does not collect, cause not named"
    return "the suite is already red at the parent commit"


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
                instance, why = validate(repo, sha, tests, env, Path(tmp))
            except (subprocess.SubprocessError, OSError, zipfile.BadZipFile) as exc:
                print(f"  {sha[:8]}  skipped: {type(exc).__name__}", flush=True)
                continue
        mark = (f"kept, {len(instance.f2p)} failing and {len(instance.p2p)} to preserve"
                if instance else why)
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
