"""Running a command many times, and knowing how many times is enough.

An intermittent failure cannot be shown fixed by one clean run, but "run it a
few more times" is not a standard either. If a bug was observed failing three
times in fifty runs, the question of how many clean runs would justify calling
it gone has an arithmetic answer, and the runtime should compute it rather than
leave the agent to guess.

None of the fourteen systems surveyed ships a repeat runner, a stress harness,
or any instrumentation for nondeterministic bugs.
"""

from __future__ import annotations

import math
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

MARKER = "EP-REPEAT"
DEFAULT_CONFIDENCE = 0.95
MIN_RUNS = 20
MAX_RUNS = 300


@dataclass
class Outcome:
    command: str
    runs: int
    passed: int
    failed: int
    seconds: float
    stopped_early: bool = False

    @property
    def rate(self) -> float:
        return self.failed / self.runs if self.runs else 0.0

    @property
    def verdict(self) -> str:
        if self.failed == 0:
            return "stable"
        if self.passed == 0:
            return "always-fails"
        return "flaky"

    def line(self) -> str:
        """One machine-readable line, so the runtime never has to guess."""
        return (
            f"{MARKER} verdict={self.verdict} runs={self.runs} passed={self.passed} "
            f"failed={self.failed} rate={self.rate:.4f} seconds={self.seconds:.1f} "
            f"early={'yes' if self.stopped_early else 'no'} cmd={self.command}"
        )

    def summary(self) -> str:
        head = f"{self.runs} runs of `{self.command}`: {self.passed} passed, {self.failed} failed"
        if self.verdict == "stable":
            return f"{head}\n  stable across {self.runs} runs ({rules_out(self.runs):.1%} failure rate ruled out)"
        if self.verdict == "always-fails":
            return f"{head}\n  fails every time, so this is not intermittent"
        return f"{head}\n  flaky at about {self.rate:.1%}; {runs_needed(self.rate)} clean runs would show it fixed"


def runs_needed(rate: float, confidence: float = DEFAULT_CONFIDENCE) -> int:
    """Clean runs required to rule out a failure of the given rate.

    If a fault still occurs with probability p, the chance of n clean runs in a
    row is (1-p)^n. Requiring that to fall below 1 - confidence gives
    n >= log(1 - confidence) / log(1 - p).
    """
    if rate <= 0:
        return MIN_RUNS
    if rate >= 1:
        return 1
    needed = math.ceil(math.log(1 - confidence) / math.log(1 - rate))
    return max(MIN_RUNS, min(MAX_RUNS, needed))


def rules_out(runs: int, confidence: float = DEFAULT_CONFIDENCE) -> float:
    """The smallest failure rate that this many clean runs makes implausible."""
    if runs <= 0:
        return 1.0
    return 1 - (1 - confidence) ** (1 / runs)


def run(command: str, times: int, cwd: Path, jobs: int = 1, timeout: int = 300,
        stop_on_fail: bool = False) -> Outcome:
    """Run one command repeatedly and count how it went."""
    started = time.perf_counter()
    passed = failed = 0
    stopped = False

    def once(_: int) -> bool:
        try:
            done = subprocess.run(command, shell=True, cwd=cwd, capture_output=True,
                                  text=True, timeout=timeout)
            return done.returncode == 0
        except subprocess.TimeoutExpired:
            return False

    if jobs > 1:
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            for ok in pool.map(once, range(times)):
                passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)
    else:
        for i in range(times):
            if once(i):
                passed += 1
            else:
                failed += 1
                if stop_on_fail:
                    stopped = True
                    break

    return Outcome(
        command=command, runs=passed + failed, passed=passed, failed=failed,
        seconds=time.perf_counter() - started, stopped_early=stopped,
    )
