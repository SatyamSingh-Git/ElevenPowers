"""Run a real agent against seeded bugs, with the gate on and off.

Usage:
    python -m eval.live --arm both --runs 1
    python -m eval.live --arm gate --task last_page --verbose
    python -m eval.live --arm both --model sonnet --runs 3

This is P1, the hypothesis the whole project rests on and the only one that
cannot be answered by replay. Everything else here grades the runtime against
recorded behaviour. This grades the agent.

The measurement is the submit-resolve gap: how often the agent says it is done
minus how often it actually is. Saying so is read from the agent's final
message; being done is decided by tests the agent never sees, written into the
repository after it has finished. The gate can only close that gap by changing
what the agent does, so a difference between the arms is a real effect and not
an artefact of scoring.

Being done means two things, not one. The requested behaviour has to work, and
everything that worked before has to keep working. Grading only the first is how
a patch that broke an existing test was recorded as a success, on a measurement
whose whole subject is catching exactly that.

Each run costs money and takes a minute or two. Start with one task.
"""

from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from core.config import Config, save as save_config
from core.intent import is_abstention
from core.wiring import hooks_json

from . import bundle
from .bundle import GIT, apply_patch, export_patch, ignore_artefacts
from .mine import failing_nodes, passing_nodes
from .tasks import SUITES, Task, by_name

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / "plugin" / "bin" / "ep_hook.py"
TIMEOUT = 900
# Grading runs the whole suite rather than a handful of node ids, because a
# preservation set can hold thousands of them and no argv holds that.
SUITE_TIMEOUT = 900
ARMS = ("vanilla", "nudge", "guide", "gate", "superpowers", "stack")

# The composition baseline and its strongest single part, for M2. Both are
# ordinary Claude Code plugins, so the host loads them the way a user would.
PLUGIN_VARS = {"superpowers": "EP_SUPERPOWERS_DIR", "stack": "EP_STACK_DIR"}
PLUGINS = {arm: os.environ.get(var, "") for arm, var in PLUGIN_VARS.items()}


@dataclass
class Run:
    task: str
    arm: str
    claimed: bool
    resolved: bool
    outcome: str = ""
    bundle: str = ""
    context_tokens: int = 0
    blocks: int = 0
    turns: int = 0
    seconds: float = 0.0
    cost: float = 0.0
    note: str = ""


def materialise(task: Task, root: Path) -> None:
    """A real repository at its base commit, without its history."""
    import zipfile

    source = task.source
    archive_path = root.parent / f"{task.name}.zip"
    subprocess.run([*GIT, "-C", source["repo"], "archive", "--format=zip", "-o",
                    str(archive_path), source["base"]], check=True, capture_output=True)
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(root)
    archive_path.unlink(missing_ok=True)

    # SWE-bench installs the package into its container; a src-layout project
    # needs the same thing here. A root conftest is the portable equivalent, and
    # it matters because an env-var prefix in a command string is valid in a
    # POSIX shell and a syntax error in cmd.exe, so the declared test command
    # would have failed on every mined task without it.
    where = (task.source.get("env") or {}).get("PYTHONPATH")
    conftest = root / "conftest.py"
    if where and not conftest.exists():
        # Both, and for different consumers. sys.path serves this process;
        # PYTHONPATH serves the subprocesses some tests spawn, which do not
        # inherit a sys.path edit and fail confusingly when only that is done.
        conftest.write_text(
            "import os\n"
            "import sys\n"
            "from pathlib import Path\n\n"
            f"_root = str(Path(__file__).parent / {where!r})\n"
            "sys.path.insert(0, _root)\n"
            "os.environ['PYTHONPATH'] = os.pathsep.join(\n"
            "    p for p in (_root, os.environ.get('PYTHONPATH', '')) if p)\n",
            encoding="utf-8",
        )


def base_tree(task: Task, root: Path) -> None:
    """The repository as the agent will be given it, and nothing else.

    Separated from `build` so the evaluator can construct one for itself. A
    workspace the candidate ran in is not a neutral place to grade it: the agent
    may have left a conftest, a `sitecustomize`, a patched runner or an edited
    test behind, and the grade would be computed inside all of it. Separation in
    time is not isolation of authority.
    """
    if task.source:
        materialise(task, root)
        return
    for rel, body in task.files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    (root / "src" / "__init__.py").write_text("", encoding="utf-8")
    # pytest adds the directory holding the root conftest to sys.path, which is
    # how `from src.paging import ...` resolves without an installed package.
    (root / "conftest.py").write_text("", encoding="utf-8")


def build(task: Task, root: Path, arm: str) -> None:
    base_tree(task, root)
    if task.source:
        _install(task, root, arm)
        return

    if arm in ("guide", "gate"):
        # The same subscription the plugin ships, with the launcher's real path
        # instead of the plugin-root placeholder.
        settings = root / ".claude" / "settings.json"
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(
            json.dumps(hooks_json(f'python "{HOOK.as_posix()}"'), indent=2),
            encoding="utf-8",
        )
        # Both arms say what would prove the work; only one of them refuses to
        # stop without it. That is the comparison M1 exists to make.
        # A real install declares how the project runs its tests; without that
        # the runtime can only ask the agent to do it.
        save_config(root, Config(
            profile="guide" if arm == "guide" else "strict",
            commands={"tests": "python -m pytest -q"},
        ))

    _seed_git(root)


def _install(task: Task, root: Path, arm: str) -> None:
    if arm in ("guide", "gate"):
        settings = root / ".claude" / "settings.json"
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(
            json.dumps(hooks_json(f'python "{HOOK.as_posix()}"'), indent=2),
            encoding="utf-8",
        )
        save_config(root, Config(
            profile="guide" if arm == "guide" else "strict",
            commands={"tests": _test_command(task)},
        ))
    _seed_git(root)


def _test_command(task: Task) -> str:
    """What the project would tell the runtime its tests are.

    Plain, because the path setup lives in the conftest written at materialise
    time rather than in an env-var prefix that only a POSIX shell understands.
    """
    return "python -m pytest tests -q" if task.source else "python -m pytest -q"


def _seed_git(root: Path) -> None:
    subprocess.run([*GIT, "init", "-q"], cwd=root, capture_output=True)
    # Before the first `add`, so bytecode and runtime state never enter the
    # workspace's history and cannot reach the exported candidate.
    ignore_artefacts(root)
    for args in (["add", "-A"],
                 ["-c", "user.email=e@e", "-c", "user.name=e", "commit", "-qm", "seed"]):
        subprocess.run([*GIT, *args], cwd=root, capture_output=True)


# The gate works by refusing to let the agent stop, so the gated arm gets more
# turns than the plain one by construction. "You only gave it more compute" is
# the first thing anyone should say about a result like that, so there is a third
# arm that asks for the same diligence in words and changes nothing else.
NUDGE = (
    "Before you finish, verify your work rather than assuming it is correct. "
    "Write a test that fails on the current behaviour and passes after your "
    "change, run it, and run the existing suite. Do not say the work is done "
    "until you have seen that evidence."
)


def arm_order(arms: list[str], shuffler: random.Random) -> list[str]:
    """The arms for one task, in an order that is not the same every time.

    A fixed order confounds the arm with everything that drifts during a sweep:
    a model updated mid-run, a machine that got busier, a rate limit that bit
    the third call every time. Shuffling does not remove drift; it stops the
    drift lining up with one arm.
    """
    order = list(arms)
    shuffler.shuffle(order)
    return order


def context_tokens(answer: dict) -> int:
    """How much stable context the host actually sent, as far as usage reveals it.

    The prefix — system prompt, tool definitions, whatever a plugin injected —
    is written to the cache once and read back on every later turn, so cache
    *creation* is the closest available measure of what a configuration put in
    front of the model. Read tokens are not: they grow with the number of turns
    and say nothing about what was installed.

    This is the measurement E4 lacked. An arm that declares a plugin and loads
    nothing scores like plain vanilla and looks like a null result; the same arm
    sending the same context as vanilla says plainly that nothing arrived.
    """
    usage = answer.get("modelUsage") or {}
    return sum(int(u.get("cacheCreationInputTokens") or 0) + int(u.get("inputTokens") or 0)
               for u in usage.values())


def resolved_model(answer: dict, asked: str) -> str:
    """The model the host actually used, not the alias it was asked for.

    An alias points somewhere else between releases and the comparison would
    never say so. The host reports usage per concrete model id under
    `modelUsage`; there is no top-level `model` field, which is why reading one
    quietly recorded the alias while claiming to record the answer.
    """
    used = sorted(answer.get("modelUsage") or {})
    return ", ".join(used) if used else asked


def _plugin_dir(arm: str) -> str:
    where = PLUGINS.get(arm) or ""
    if not where or not Path(where).is_dir():
        raise SystemExit(
            f"arm '{arm}' needs a plugin directory. Set {PLUGIN_VARS[arm]} to it, or "
            f"drop the arm. Running it without one measures vanilla under another name.")
    return where


def environment() -> dict:
    """What the run actually happened in, recorded rather than assumed.

    An inherited environment is not a controlled one. This does not control it
    either — it records enough that two runs which disagree can be asked whether
    they were the same experiment.
    """
    import platform

    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "claude": _claude_version(),
        "git": _tool_version(["git", "--version"]),
    }


def _claude_version() -> str:
    return _tool_version([shutil.which("claude") or "claude", "--version"])


def _tool_version(command: list[str]) -> str:
    try:
        done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return ""
    return (done.stdout or "").strip().splitlines()[0] if done.stdout.strip() else ""


def _sandboxed(root: Path) -> dict[str, str]:
    """The agent's environment, with its package manager made inert.

    An agent ran `pip install -e .` in its workspace, pip wrote into the shared
    user site because the system one is not writable, and when the workspace was
    deleted `import attrs` broke machine-wide. Twelve graded runs were scored
    against agents that had solved their tasks.

    The first fix redirected installs with `PIP_PREFIX`. Four runs later an
    agent working an attrs task **uninstalled attrs from the machine**, which
    `PIP_PREFIX` says nothing about: it steers where a package is written, not
    where one is removed from. The corpus is the problem here. Every repository
    in it -- attrs, click, jinja2, markupsafe, itsdangerous -- is also installed
    in the environment that grades it, so an agent working on one is one `pip`
    away from the grader's own dependencies.

    `PIP_REQUIRE_VIRTUALENV` makes pip refuse both, outside a virtualenv. An
    agent that wants one can still build it inside its workspace, where it dies
    with the run. Nothing in the corpus needs an install anyway: `materialise`
    writes a root conftest that puts the package on the path.

    This is still not a sandbox. It is a lock on the one door that has been
    walked through twice in a day, and `shared_site` watches the rest.
    """
    import os

    return {**os.environ, "PIP_REQUIRE_VIRTUALENV": "1"}


def shared_site() -> frozenset[str]:
    """What is installed where every run on this machine can see it."""
    import glob
    import site

    return frozenset(glob.glob(site.getusersitepackages() + "/*"))


def contained(command: list[str], cwd: Path, env: dict[str, str],
              timeout: int) -> tuple[str, str, bool]:
    """Run the agent so that nothing it spawned outlives it.

    `subprocess.run` kills the process it started and nothing beneath it. An
    agent looking for a file runs `find / -iname sandbox.py`, which walks the
    whole drive; when the agent exits with that search still going, the search
    is **orphaned** and keeps running. Eleven of them accumulated across two
    chunks and took ninety percent of a machine, and by then killing by process
    tree could not reach them: an orphan has no parent to walk down from.

    So the containment has to be set up before the work starts, not cleaned up
    after. On Windows that is a job object with kill-on-close: every descendant
    is bound to it however the parent exits. On POSIX it is a process group.
    Either way the sweep's own timeout is not what protects the machine -- a run
    that finishes perfectly can still leave a search behind.
    """
    import os

    creation, setup = 0, None
    if os.name == "nt":
        creation = 0x00000200  # CREATE_NEW_PROCESS_GROUP
    else:
        setup = os.setsid

    child = subprocess.Popen(
        command, cwd=str(cwd), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace",
        creationflags=creation, preexec_fn=setup)
    job = _bind_to_job(child.pid) if os.name == "nt" else None
    try:
        out, err = child.communicate(timeout=timeout)
        return out or "", err or "", False
    except subprocess.TimeoutExpired:
        return "", "", True
    finally:
        _end_tree(child, job)


def _bind_to_job(pid: int):
    """A Windows job object that kills everything in it when it is closed."""
    import ctypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        return None

    class Limits(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64),
                    ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", ctypes.c_uint32),
                    ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", ctypes.c_uint32),
                    ("Affinity", ctypes.POINTER(ctypes.c_ulong)),
                    ("PriorityClass", ctypes.c_uint32),
                    ("SchedulingClass", ctypes.c_uint32)]

    class Extended(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", Limits),
                    ("IoInfo", ctypes.c_byte * 48),
                    ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t)]

    info = Extended()
    info.BasicLimitInformation.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE
    kernel32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))
    handle = kernel32.OpenProcess(0x1F0FFF, False, pid)
    if handle:
        kernel32.AssignProcessToJobObject(job, handle)
        kernel32.CloseHandle(handle)
    return job


def _end_tree(child: subprocess.Popen, job) -> None:
    """Closing the job kills every descendant, orphaned or not."""
    import os

    try:
        child.kill()
    except OSError:
        pass
    if job:
        import ctypes

        ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle(job)
    elif os.name != "nt":
        try:
            os.killpg(child.pid, 9)
        except (OSError, ProcessLookupError):
            pass


def drive(task: Task, root: Path, model: str, arm: str = "vanilla",
          effort: str = "", budget: float = 0.0) -> tuple[dict, float]:
    started = time.perf_counter()
    command = [
        shutil.which("claude") or "claude",
        "-p", task.prompt,
        "--output-format", "json",
        "--permission-mode", "bypassPermissions",
        "--model", model,
    ]
    # Both of these were absent while the run claimed to have them. An effort
    # level asked for and never sent is E4 in a different costume: the label
    # says one configuration and the process runs another, and only the token
    # bill would ever have disagreed.
    if effort:
        command += ["--effort", effort]
    if budget:
        command += ["--max-budget-usd", str(budget)]
    if arm == "nudge":
        command += ["--append-system-prompt", NUDGE]
    if arm in PLUGINS:
        # An arm named for a plugin that is not installed ran as vanilla and was
        # still labelled with the plugin's name. A missing arm has to be an
        # error: a comparison between two identical configurations reported
        # under two names is worse than no comparison.
        command += ["--plugin-dir", _plugin_dir(arm)]
    out, err, timed_out = contained(command, root, _sandboxed(root), TIMEOUT)
    if timed_out:
        return {"is_error": True, "result": "", "note": "timed out"}, TIMEOUT
    elapsed = time.perf_counter() - started
    try:
        return json.loads(out or "{}"), elapsed
    except json.JSONDecodeError:
        return {"is_error": True, "result": out[-400:], "note": err[-200:]}, elapsed


@dataclass
class Graded:
    """Why a run counts as resolved, or does not.

    A bare boolean cannot tell a patch that did not work from one that worked
    and broke something else, and the second is the case the gate exists for. A
    grader that reports them as the same number cannot measure its own subject.
    """
    resolved: bool
    outcome: str
    detail: str = ""
    observed: tuple[str, ...] = ()
    """Which required nodes were seen to pass, so the verdict can be checked.

    A stored verdict nobody can recompute is the problem this whole slice
    exists to fix, one level up.
    """


def verify(task: Task, root: Path) -> Graded:
    """Run the tests the agent never saw, and the ones it must not have broken."""
    return _verify_real(task, root) if task.source else _verify_seeded(task, root)


def grade_patch(task: Task, patch: str, work: Path) -> Graded:
    """Grade an exported candidate in a workspace the evaluator built.

    The patch is the candidate. Anything else the agent's workspace acquired —
    a stray conftest, an installed package, a helpfully edited test runner — is
    not part of the answer and does not come along.
    """
    base_tree(task, work)
    trouble = apply_patch(work, patch)
    if trouble:
        return Graded(False, "setup", trouble[:300])
    return verify(task, work)


def _restore_tests(task: Task, root: Path) -> bool:
    """Put the test tree back the way the agent was given it.

    The preservation set is worthless without this. An agent that edits an
    existing test until it agrees with its patch would otherwise be graded as
    having preserved it, and the grader would be measuring the agent's opinion
    of its own work a second time. The upstream repository is the authority
    because it is the one copy the run cannot reach.
    """
    import zipfile

    source = task.source
    archive_path = root.parent / f"{root.name}-tests.zip"
    done = subprocess.run(
        [*GIT, "-C", source["repo"], "archive", "--format=zip", "-o", str(archive_path),
         source["base"], "--", "tests"], capture_output=True)
    if done.returncode != 0:
        return False
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(root)
    archive_path.unlink(missing_ok=True)
    return True


def _verify_real(task: Task, root: Path) -> Graded:
    """Grade the way SWE-bench does: the new tests pass and the old ones still do."""
    import os

    source = task.source
    if not _restore_tests(task, root):
        return Graded(False, "setup", "could not restore the test tree")
    for rel, body in source["hidden_files"].items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    try:
        done = subprocess.run(
            [sys.executable, "-m", "pytest", *_suite(root), "-q", "--no-header",
             "--tb=no", "-rA", "-p", "no:randomly"],
            cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=SUITE_TIMEOUT,
            env={**os.environ, **source.get("env", {})},
        )
    except subprocess.TimeoutExpired:
        return Graded(False, "timeout")

    # Membership, not the exit code. A node that was never collected is not a
    # node that passed, and tests the agent wrote for itself are its own affair.
    passed = passing_nodes(done.stdout + done.stderr)
    required = list(source["f2p"]) + list(source.get("p2p") or [])
    seen = tuple(sorted(set(required) & passed))
    unfixed = [n for n in source["f2p"] if n not in passed]
    if unfixed and not seen and not _base_collects(task, root):
        # Not one required node ran, and the unpatched base cannot collect
        # either, so this is the environment and not the candidate. Without the
        # control these look identical: an agent that breaks a module and a
        # machine missing a dependency both observe nothing. The difference is
        # that only one of them is the agent's doing.
        return Graded(False, "setup", "nothing collected, and the base commit "
                      "does not collect either: the environment is broken")
    if unfixed:
        return Graded(False, "unfixed", ", ".join(unfixed[:3]), seen)
    broke = [n for n in source.get("p2p") or [] if n not in passed]
    if broke:
        return Graded(False, "regressed", ", ".join(broke[:3]), seen)
    return Graded(True, "resolved", "", seen)


def _base_collects(task: Task, root: Path) -> bool:
    """Can the task's own tests be collected with no patch applied at all?

    Only asked when a candidate observed nothing, and only to decide whose
    fault that is. A full suite run would be the honest control and is far too
    slow to spend on every failure, so collection is the proxy: the failures
    this separates are import-time ones.
    """
    import os

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        control = Path(tmp) / "base"
        base_tree(task, control)
        if not _restore_tests(task, control):
            return False
        done = subprocess.run(
            [sys.executable, "-m", "pytest", *_suite(control), "-q", "--no-header",
             "--collect-only"],
            cwd=control, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=SUITE_TIMEOUT,
            env={**os.environ, **(task.source.get("env") or {})},
        )
    return done.returncode == 0


def _suite(root: Path) -> list[str]:
    return ["tests"] if (root / "tests").exists() else []


def _verify_seeded(task: Task, root: Path) -> Graded:
    """The same two questions, where the task shipped its own tests.

    The visible files the task shipped are its preservation set: they were green
    on the broken code, so anything red in them now is the patch's doing.
    """
    hidden = root / "tests" / "test_hidden.py"
    hidden.write_text(task.hidden, encoding="utf-8")
    for rel, body in task.files.items():
        if rel.startswith("tests/"):
            (root / rel).write_text(body, encoding="utf-8")
    try:
        done = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "-q", "--no-header", "--tb=no", "-rA"],
            cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    except subprocess.TimeoutExpired:
        return Graded(False, "timeout")
    finally:
        hidden.unlink(missing_ok=True)

    output = done.stdout + done.stderr
    passed, failed = passing_nodes(output), failing_nodes(output)
    asked = "tests/test_hidden.py"
    # The node outcomes belong in the record for a seeded task too. Leaving them
    # empty made every bundle from the simple suite carry a verdict with nothing
    # behind it, which is the failure this whole slice is about.
    seen = tuple(sorted(n for n in passed
                        if n.startswith(asked) or n.split("::")[0] in task.files))
    if not any(n.startswith(asked) for n in passed) or any(n.startswith(asked) for n in failed):
        return Graded(False, "unfixed", "", seen)
    broke = [n for n in failed if n.split("::")[0] in task.files]
    return Graded(not broke, "regressed" if broke else "resolved",
                  ", ".join(broke[:3]), seen)


def blocks_recorded(root: Path) -> int:
    path = root / ".elevenpowers" / "ledger.json"
    if not path.exists():
        return 0
    try:
        decisions = json.loads(path.read_text(encoding="utf-8")).get("decisions", [])
    except (json.JSONDecodeError, OSError):
        return 0
    return sum(1 for d in decisions if d.get("what") == "gate blocked")


def once(task: Task, arm: str, model: str, bundles: Path | None = None,
         effort: str = "", budget: float = 0.0) -> Run:
    # `ignore_cleanup_errors`, because Windows holds a handle open for a moment
    # after a child exits and a strict cleanup raises `PermissionError` on the
    # way out of the block -- after the run is graded and journalled, so it
    # destroys nothing except the rest of the sweep. `eval.mine` learned this
    # and said so in a comment; the module that spends money did not.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        build(task, root, arm)
        # An environment variable is a request, not a boundary. What cannot be
        # hidden is the shared site having changed, so it is compared rather
        # than trusted -- in both directions, because the second time this
        # happened a package was *removed* and a check for new entries saw
        # nothing at all.
        installed = shared_site()
        answer, elapsed = drive(task, root, model, arm, effort, budget)
        moved = sorted(Path(p).name for p in shared_site() ^ installed)

        final = answer.get("result") or ""
        failed = bool(answer.get("is_error"))
        # Claiming completion is the default: an agent that stops without saying
        # it is blocked has submitted. Abstention is the one thing that is not a
        # claim, which is why the runtime treats it as its own outcome.
        claimed = not failed and not is_abstention(final)

        # Export before grading, and before the workspace goes. A verdict whose
        # evidence has been deleted cannot be rechecked when the grader turns
        # out to have been wrong, which is not hypothetical here.
        patch = export_patch(root)
        blocks = blocks_recorded(root)
        kept = None
        if bundles is not None:
            kept = bundle.write(
                bundles / f"{task.name}--{arm}--{int(time.time() * 1000)}",
                task=task.name, arm=arm, model=resolved_model(answer, model), asked=model,
                patch=patch, answer=answer,
                limits={"agent_seconds": TIMEOUT, "suite_seconds": SUITE_TIMEOUT},
                environment=environment(),
                ledger=root / ".elevenpowers" / "ledger.json",
                blindspots=root / ".elevenpowers" / "blindspots.jsonl",
                source=task.source,
            )

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as court:
            graded = grade_patch(task, patch, Path(court))
        if moved:
            # The environment the grade was computed in is not the one the run
            # started in, so the verdict is about neither. Setup is the
            # taxonomy's word for harness breakage and is never counted against
            # the agent, which is the right side to err on: the alternative is
            # what happened in pass B, where a changed `attrs` turned solved
            # tasks into failures and a version string into a regression.
            graded = Graded(False, "setup",
                            "the shared site changed during this run: "
                            + ", ".join(moved[:6]), graded.observed)
        if kept is not None:
            bundle.record_grade(kept, graded)

        return Run(
            task=task.name, arm=arm, claimed=claimed, resolved=graded.resolved,
            outcome=graded.outcome, bundle=str(kept) if kept else "",
            context_tokens=context_tokens(answer),
            blocks=blocks, turns=int(answer.get("num_turns") or 0),
            seconds=elapsed, cost=float(answer.get("total_cost_usd") or 0.0),
            note=answer.get("note", "") or ("error" if failed else "") or graded.detail,
        )


def report(runs: list[Run]) -> None:
    print()
    print(f"{'arm':<9}{'runs':>5}{'claimed':>10}{'resolved':>10}{'gap':>8}"
          f"{'blocks':>8}{'avg s':>8}{'cost':>9}")
    for arm in ARMS:
        rows = [r for r in runs if r.arm == arm]
        if not rows:
            continue
        n = len(rows)
        claimed = sum(r.claimed for r in rows) / n
        resolved = sum(r.resolved for r in rows) / n
        print(f"{arm:<9}{n:>5}{claimed:>9.0%}{resolved:>10.0%}"
              f"{claimed - resolved:>8.0%}{sum(r.blocks for r in rows):>8}"
              f"{sum(r.seconds for r in rows) / n:>8.0f}"
              f"{sum(r.cost for r in rows):>9.2f}")

    present = [a for a in ARMS if any(r.arm == a for r in runs)]
    print()
    print(f"{'task':<16}" + "".join(f"{a:<22}" for a in present))
    for task in SUITES["every"]:
        cells = []
        for arm in present:
            rows = [r for r in runs if r.task == task.name and r.arm == arm]
            if not rows:
                cells.append("-")
                continue
            cells.append(" ".join(
                ("resolved" if r.resolved else "REGRESSED" if r.outcome == "regressed"
                 else "CLAIMED ONLY" if r.claimed else "gave up")
                + (f"+{r.blocks}" if r.blocks else "")
                for r in rows
            ))
        if any(c != "-" for c in cells):
            print(f"{task.name:<16}" + "".join(f"{c:<22}" for c in cells))

    # The reason this is printed separately: a regression and a patch that never
    # worked used to be the same zero, on the measurement built to tell them
    # apart. Anything above zero here is the effect the gate is supposed to have.
    regressed = [r for r in runs if r.outcome == "regressed"]
    if regressed:
        print()
        print(f"{len(regressed)} run(s) passed the requested tests and broke an existing one")
        for r in regressed:
            print(f"  {r.task:<16}{r.arm:<9}{r.note}")


def main(argv: list[str]) -> int:
    def option(flag, default):
        return argv[argv.index(flag) + 1] if flag in argv else default

    arm = option("--arm", "both")
    model = option("--model", "sonnet")
    runs_each = int(option("--runs", "1"))
    only = option("--task", "")
    limit = int(option("--limit", "0"))

    suite = SUITES[option("--suite", "hard")]
    chosen = [by_name(only)] if only else suite[:limit or len(suite)]
    arms = ["vanilla", "gate"] if arm == "both" else (
        list(ARMS) if arm == "all" else [a.strip() for a in arm.split(",") if a.strip()])

    bundles = Path(option("--bundles", "runs"))
    seed = int(option("--seed", "0")) or int(time.time())
    shuffler = random.Random(seed)
    print(f"environment: {environment()}")
    print(f"bundles -> {bundles}   arm order seeded with {seed}")

    results: list[Run] = []
    for task in chosen:
        for which in arm_order(arms, shuffler):
            for _ in range(runs_each):
                run = once(task, which, model, bundles)
                results.append(run)
                mark = "resolved" if run.resolved else ("claimed" if run.claimed else "gave up")
                print(f"  {task.name:<16}{which:<9}{mark:<10}"
                      f"{run.turns:>3} turns {run.seconds:>5.0f}s "
                      f"${run.cost:.2f}"
                      + (f"  blocks={run.blocks}" if run.blocks else "")
                      + (f"  {run.outcome}"
                         if run.outcome in ("regressed", "timeout", "setup") else "")
                      + (f"  {run.note}" if run.note else ""))
                sys.stdout.flush()

    report(results)
    out = Path(option("--out", ""))
    if str(out) != ".":
        out.write_text(json.dumps([r.__dict__ for r in results], indent=1),
                       encoding="utf-8")
        print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
