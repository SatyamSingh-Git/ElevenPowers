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
message; being done is decided by a test the agent never sees, written into the
repository after it has finished. The gate can only close that gap by changing
what the agent does, so a difference between the arms is a real effect and not
an artefact of scoring.

Each run costs money and takes a minute or two. Start with one task.
"""

from __future__ import annotations

import json
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

from .tasks import SUITES, Task, by_name

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / "plugin" / "bin" / "ep_hook.py"
TIMEOUT = 900
ARMS = ("vanilla", "nudge", "guide", "gate")


@dataclass
class Run:
    task: str
    arm: str
    claimed: bool
    resolved: bool
    blocks: int = 0
    turns: int = 0
    seconds: float = 0.0
    cost: float = 0.0
    note: str = ""


def build(task: Task, root: Path, arm: str) -> None:
    for rel, body in task.files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    (root / "src" / "__init__.py").write_text("", encoding="utf-8")
    # pytest adds the directory holding the root conftest to sys.path, which is
    # how `from src.paging import ...` resolves without an installed package.
    (root / "conftest.py").write_text("", encoding="utf-8")

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
        save_config(root, Config(profile="guide" if arm == "guide" else "strict"))

    for args in (["init", "-q"], ["add", "-A"],
                 ["-c", "user.email=e@e", "-c", "user.name=e", "commit", "-qm", "seed"]):
        subprocess.run(["git", *args], cwd=root, capture_output=True)


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


def drive(task: Task, root: Path, model: str, arm: str = "vanilla") -> tuple[dict, float]:
    started = time.perf_counter()
    command = [
        shutil.which("claude") or "claude",
        "-p", task.prompt,
        "--output-format", "json",
        "--permission-mode", "bypassPermissions",
        "--model", model,
    ]
    if arm == "nudge":
        command += ["--append-system-prompt", NUDGE]
    try:
        done = subprocess.run(command, cwd=root, capture_output=True, text=True,
                              timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"is_error": True, "result": "", "note": "timed out"}, TIMEOUT
    elapsed = time.perf_counter() - started
    try:
        return json.loads(done.stdout or "{}"), elapsed
    except json.JSONDecodeError:
        return {"is_error": True, "result": done.stdout[-400:],
                "note": (done.stderr or "")[-200:]}, elapsed


def verify(task: Task, root: Path) -> bool:
    """Run the test the agent never saw."""
    path = root / "tests" / "test_hidden.py"
    path.write_text(task.hidden, encoding="utf-8")
    try:
        done = subprocess.run([sys.executable, "-m", "pytest", str(path), "-q"],
                              cwd=root, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return False
    finally:
        path.unlink(missing_ok=True)
    return done.returncode == 0


def blocks_recorded(root: Path) -> int:
    path = root / ".elevenpowers" / "ledger.json"
    if not path.exists():
        return 0
    try:
        decisions = json.loads(path.read_text(encoding="utf-8")).get("decisions", [])
    except (json.JSONDecodeError, OSError):
        return 0
    return sum(1 for d in decisions if d.get("what") == "gate blocked")


def once(task: Task, arm: str, model: str, keep: Path | None = None) -> Run:
    with tempfile.TemporaryDirectory(dir=keep) as tmp:
        root = Path(tmp)
        build(task, root, arm)
        answer, elapsed = drive(task, root, model, arm)

        final = answer.get("result") or ""
        failed = bool(answer.get("is_error"))
        # Claiming completion is the default: an agent that stops without saying
        # it is blocked has submitted. Abstention is the one thing that is not a
        # claim, which is why the runtime treats it as its own outcome.
        claimed = not failed and not is_abstention(final)
        return Run(
            task=task.name, arm=arm, claimed=claimed, resolved=verify(task, root),
            blocks=blocks_recorded(root), turns=int(answer.get("num_turns") or 0),
            seconds=elapsed, cost=float(answer.get("total_cost_usd") or 0.0),
            note=answer.get("note", "") or ("error" if failed else ""),
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
    for task in SUITES["all"]:
        cells = []
        for arm in present:
            rows = [r for r in runs if r.task == task.name and r.arm == arm]
            if not rows:
                cells.append("-")
                continue
            cells.append(" ".join(
                ("resolved" if r.resolved else "CLAIMED ONLY" if r.claimed else "gave up")
                + (f"+{r.blocks}" if r.blocks else "")
                for r in rows
            ))
        if any(c != "-" for c in cells):
            print(f"{task.name:<16}" + "".join(f"{c:<22}" for c in cells))


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
        list(ARMS) if arm == "all" else [arm])

    results: list[Run] = []
    for task in chosen:
        for which in arms:
            for _ in range(runs_each):
                run = once(task, which, model)
                results.append(run)
                mark = "resolved" if run.resolved else ("claimed" if run.claimed else "gave up")
                print(f"  {task.name:<16}{which:<9}{mark:<10}"
                      f"{run.turns:>3} turns {run.seconds:>5.0f}s "
                      f"${run.cost:.2f}"
                      + (f"  blocks={run.blocks}" if run.blocks else "")
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
