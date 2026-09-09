"""Claim types, risk tiers, and the obligations each combination requires.

This table is the contract. It is data rather than code so that changing what
counts as proof does not mean changing the gate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from .evidence import Evidence, Kind, Result


class Claim(str, Enum):
    BUG_FIXED = "bug_fixed"
    FEATURE_ADDED = "feature_added"
    REFACTOR_SAFE = "refactor_safe"
    MIGRATION_SAFE = "migration_safe"
    PERF_IMPROVED = "perf_improved"
    DEPS_UPDATED = "deps_updated"
    DOCS_CHANGED = "docs_changed"
    CANNOT_COMPLETE = "cannot_complete"


class Risk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


TEST_FILE = re.compile(r"(test_|_test\.|\.test\.|\.spec\.|::)")


@dataclass(frozen=True)
class Obligation:
    key: str
    kind: Kind
    description: str
    hint: str
    require_pass: bool = True
    require_prior_failure: bool = False
    scoped: bool = False

    def matches(self, e: Evidence) -> bool:
        """Whether a record is the right shape for this obligation.

        A `scoped` obligation wants evidence about a particular test rather than
        a whole-suite run. A run of one test file counts: `pytest -q` prints no
        per-test lines, so demanding a node-level record would fail agents that
        did exactly the right thing.
        """
        if e.kind is self.kind:
            return not self.scoped or TEST_FILE.search(e.identity) is not None
        if self.scoped and self.kind is Kind.TEST and e.kind is Kind.SUITE:
            return TEST_FILE.search(e.identity) is not None
        return False

    def satisfied_by(self, records: list[Evidence]) -> Evidence | None:
        candidates = [e for e in records if self.matches(e)]
        if self.require_pass:
            candidates = [e for e in candidates if e.result is Result.PASS]
        return candidates[-1] if candidates else None


TEST_ADDED = Obligation(
    "test_added", Kind.TEST,
    "a test covering the change passes",
    "run the test that exercises this change, by name or by file",
    scoped=True,
)
TEST_FAILED_FIRST = Obligation(
    "reproduced", Kind.TEST,
    "that test failed before the fix",
    "run it before applying the fix so the failure is on record",
    require_pass=False, require_prior_failure=True, scoped=True,
)
SUITE_GREEN = Obligation(
    "suite_green", Kind.SUITE,
    "the related test suite passes",
    "run the suite covering the files you changed",
)
BUILD_OK = Obligation(
    "build_ok", Kind.BUILD,
    "the project builds",
    "run the build command",
)
TYPECHECK_OK = Obligation(
    "typecheck_ok", Kind.TYPECHECK,
    "type checking is clean",
    "run the type checker",
)
RUNTIME_OK = Obligation(
    "runtime_ok", Kind.RUNTIME,
    "the behaviour was observed working",
    "run the reproduction and show it no longer fails",
)
STABLE = Obligation(
    "stable", Kind.RUNTIME,
    "repeated runs are stable",
    "use the repeat runner to show the failure no longer occurs across runs",
)
BENCH = Obligation(
    "benchmark", Kind.BENCHMARK,
    "a benchmark before and after",
    "run the benchmark on both sides of the change",
)
REASON = Obligation(
    "reason", Kind.DIFF,
    "a stated reason and what was tried",
    "record why this cannot be completed as asked",
    require_pass=False,
)

TABLE: dict[Claim, dict[Risk, list[Obligation]]] = {
    Claim.BUG_FIXED: {
        Risk.LOW: [TEST_ADDED, SUITE_GREEN],
        Risk.MEDIUM: [TEST_ADDED, TEST_FAILED_FIRST, SUITE_GREEN],
        Risk.HIGH: [TEST_ADDED, TEST_FAILED_FIRST, SUITE_GREEN, STABLE],
    },
    Claim.FEATURE_ADDED: {
        Risk.LOW: [SUITE_GREEN],
        Risk.MEDIUM: [TEST_ADDED, SUITE_GREEN, TYPECHECK_OK],
        Risk.HIGH: [TEST_ADDED, SUITE_GREEN, TYPECHECK_OK, BUILD_OK],
    },
    Claim.REFACTOR_SAFE: {
        Risk.LOW: [SUITE_GREEN],
        Risk.MEDIUM: [SUITE_GREEN, TYPECHECK_OK],
        Risk.HIGH: [SUITE_GREEN, TYPECHECK_OK, BUILD_OK],
    },
    Claim.MIGRATION_SAFE: {
        Risk.LOW: [RUNTIME_OK],
        Risk.MEDIUM: [RUNTIME_OK, SUITE_GREEN],
        Risk.HIGH: [RUNTIME_OK, SUITE_GREEN, STABLE],
    },
    Claim.PERF_IMPROVED: {
        Risk.LOW: [BENCH],
        Risk.MEDIUM: [BENCH, SUITE_GREEN],
        Risk.HIGH: [BENCH, SUITE_GREEN, STABLE],
    },
    Claim.DEPS_UPDATED: {
        Risk.LOW: [SUITE_GREEN],
        Risk.MEDIUM: [SUITE_GREEN, BUILD_OK],
        Risk.HIGH: [SUITE_GREEN, BUILD_OK, TYPECHECK_OK],
    },
    Claim.DOCS_CHANGED: {Risk.LOW: [], Risk.MEDIUM: [], Risk.HIGH: []},
    Claim.CANNOT_COMPLETE: {Risk.LOW: [REASON], Risk.MEDIUM: [REASON], Risk.HIGH: [REASON]},
}

RISKY_PATHS = [
    (re.compile(r"(^|/)(migrations?|alembic|schema)/"), "migration"),
    (re.compile(r"(^|/)(auth|session|login|oauth|jwt|password|crypto)"), "auth"),
    (re.compile(r"(^|/)(billing|payment|stripe|checkout|invoice|charge)"), "payments"),
    (re.compile(r"(^|/)(\.github/workflows|deploy|terraform|helm|k8s|infra)/"), "infra"),
    (re.compile(r"(^|/)(secrets?|credentials?|\.env)"), "secrets"),
]


def risk_of(paths: list[str], changed_lines: int = 0) -> tuple[Risk, list[str]]:
    """Risk tier from the paths a task touches. Deterministic, no model call."""
    domains = sorted({name for p in paths for pattern, name in RISKY_PATHS if pattern.search(p)})
    if domains:
        return Risk.HIGH, domains
    if len(paths) > 10 or changed_lines > 300:
        return Risk.MEDIUM, []
    return (Risk.MEDIUM if len(paths) > 3 else Risk.LOW), []


def obligations_for(claim: Claim, risk: Risk) -> list[Obligation]:
    return TABLE[claim][risk]
