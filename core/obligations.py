"""Claim types, risk tiers, and the obligations each combination requires.

Two rules govern this table, both learned by measuring a version that ignored
them and produced a 75 percent false-block rate:

1. An obligation must be dischargeable by an agent doing a good job. If the
   project has no test suite, demanding suite evidence is a guaranteed false
   block, so obligations are filtered by what the project can actually prove.
2. Expensive obligations need a specific trigger. Repeated-run stability is
   only meaningful for nondeterministic bugs, so it is triggered by the request
   describing intermittency, not by a risk tier.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from .evidence import Evidence, Kind, Result
from .surface import Surface


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


# A scoped identity names one test file or one test node. A bare directory such
# as `tests` is a whole-suite run and must not count as evidence that a specific
# covering test was exercised.
TEST_FILE = re.compile(
    r"::|(^|/)(test_[^/]+|[^/]*_test|[^/]*\.test|[^/]*\.spec|[^/]*_spec)\.[A-Za-z]+$"
)


@dataclass(frozen=True)
class Obligation:
    key: str
    kind: Kind
    description: str
    hint: str
    require_pass: bool = True
    require_prior_failure: bool = False
    scoped: bool = False
    broad: bool = False
    fixed_transition: bool = False
    needs: str = ""

    def available(self, surface: Surface) -> bool:
        return not self.needs or surface.supports(self.needs)

    def matches(self, e: Evidence) -> bool:
        """Whether a record is the right shape for this obligation.

        A `scoped` obligation wants evidence about a particular test rather than
        a whole-suite run: `pytest -q` prints no per-test lines, so demanding a
        node-level record would fail agents that did exactly the right thing.
        A `broad` obligation wants the opposite, since running one test file
        proves nothing about the rest of the suite.
        """
        if self.broad:
            return e.kind is self.kind and not self._is_scoped(e)
        if e.kind is self.kind:
            return not self.scoped or self._is_scoped(e)
        if self.scoped and self.kind is Kind.TEST and e.kind is Kind.SUITE:
            return self._is_scoped(e)
        return False

    @staticmethod
    def _is_scoped(e: Evidence) -> bool:
        if TEST_FILE.search(e.identity):
            return True
        # `go test -run TestX`, `pytest -k login`, `cargo test parser`: the
        # command names a selector, so the run was narrowed to specific tests.
        if re.search(r"\s-(-run|run|k|-filter|-name)[\s=]|\s-t\s", e.command):
            return True
        return bool(re.match(r"^\s*(cargo|go|swift)\s+test\s+[A-Za-z_][\w:]*\s*$", e.command))

    def satisfied_by(self, records: list[Evidence]) -> Evidence | None:
        candidates = [e for e in records if self.matches(e)]
        if self.require_pass:
            candidates = [e for e in candidates if e.result is Result.PASS]
        if candidates:
            return candidates[-1]
        if self.fixed_transition:
            return _demonstrated_fix(records)
        return None


def _demonstrated_fix(records: list[Evidence]) -> Evidence | None:
    """A test target that was failing and is now passing.

    Where tests run through an opaque wrapper such as tox or make, no scoped
    record is obtainable at all. Watching one target go from red to green is the
    same proof by a different route, and refusing it blocks agents who did the
    work correctly with the tools their project gives them.
    """
    by_identity: dict[str, list[Evidence]] = {}
    for e in records:
        if e.kind in (Kind.TEST, Kind.SUITE):
            by_identity.setdefault(e.identity, []).append(e)
    for runs in by_identity.values():
        runs.sort(key=lambda e: e.at)
        if runs[0].result is not Result.PASS and runs[-1].result is Result.PASS:
            return runs[-1]
    return None


TEST_ADDED = Obligation(
    "test_added", Kind.TEST,
    "a test covering the change passes",
    "run the test that exercises this change, by name or by file",
    scoped=True, fixed_transition=True, needs="tests",
)
TEST_FAILED_FIRST = Obligation(
    "reproduced", Kind.TEST,
    "that test failed before the fix",
    "run it before applying the fix so the failure is on record",
    require_pass=False, require_prior_failure=True, scoped=True, needs="tests",
)
SUITE_GREEN = Obligation(
    "suite_green", Kind.SUITE,
    "the related test suite passes",
    "run the suite covering the files you changed, not just the one test",
    broad=True, needs="tests",
)
BUILD_OK = Obligation(
    "build_ok", Kind.BUILD, "the project builds", "run the build command", needs="build",
)
TYPECHECK_OK = Obligation(
    "typecheck_ok", Kind.TYPECHECK, "type checking is clean", "run the type checker",
    needs="typecheck",
)
RUNTIME_OK = Obligation(
    "runtime_ok", Kind.RUNTIME,
    "the behaviour was observed working",
    "run it and show the result",
)
STABLE = Obligation(
    "stable", Kind.STABILITY,
    "repeated runs show the failure is gone",
    "ep-repeat <n> -- <the command that reproduced it>",
)
BENCH = Obligation(
    "benchmark", Kind.BENCHMARK,
    "a measurement before and after",
    "run the benchmark on both sides of the change",
)
REASON = Obligation(
    "reason", Kind.DIFF,
    "a stated reason and what was tried",
    "say what blocks this and what you attempted",
    require_pass=False,
)

TABLE: dict[Claim, dict[Risk, list[Obligation]]] = {
    Claim.BUG_FIXED: {
        Risk.LOW: [TEST_ADDED, SUITE_GREEN],
        Risk.MEDIUM: [TEST_ADDED, SUITE_GREEN],
        Risk.HIGH: [TEST_ADDED, TEST_FAILED_FIRST, SUITE_GREEN],
    },
    Claim.FEATURE_ADDED: {
        Risk.LOW: [SUITE_GREEN],
        Risk.MEDIUM: [SUITE_GREEN, TYPECHECK_OK],
        Risk.HIGH: [TEST_ADDED, SUITE_GREEN, TYPECHECK_OK],
    },
    Claim.REFACTOR_SAFE: {
        Risk.LOW: [SUITE_GREEN],
        Risk.MEDIUM: [SUITE_GREEN, TYPECHECK_OK],
        Risk.HIGH: [SUITE_GREEN, TYPECHECK_OK, BUILD_OK],
    },
    Claim.MIGRATION_SAFE: {
        Risk.LOW: [RUNTIME_OK],
        Risk.MEDIUM: [RUNTIME_OK],
        Risk.HIGH: [RUNTIME_OK, SUITE_GREEN],
    },
    Claim.PERF_IMPROVED: {
        Risk.LOW: [BENCH],
        Risk.MEDIUM: [BENCH],
        Risk.HIGH: [BENCH, SUITE_GREEN],
    },
    Claim.DEPS_UPDATED: {
        Risk.LOW: [SUITE_GREEN],
        Risk.MEDIUM: [SUITE_GREEN],
        Risk.HIGH: [SUITE_GREEN, BUILD_OK],
    },
    Claim.DOCS_CHANGED: {Risk.LOW: [], Risk.MEDIUM: [], Risk.HIGH: []},
    Claim.CANNOT_COMPLETE: {Risk.LOW: [REASON], Risk.MEDIUM: [REASON], Risk.HIGH: [REASON]},
}

# A directory component, not a substring: `src/auth/session.py` is authentication
# code, `src/oauth_button.tsx` is a button. Matching filenames put every toy
# project with an auth.py into the highest tier.
RISKY_DIRS = [
    (re.compile(r"(^|/)(migrations?|alembic|schema)(/|$)"), "migration"),
    (re.compile(r"(^|/)(auth|authentication|session|identity|oauth|crypto|security)(/|$)"), "auth"),
    (re.compile(r"(^|/)(billing|payments?|stripe|checkout|invoicing)(/|$)"), "payments"),
    (re.compile(r"(^|/)(\.github/workflows|deploy|terraform|helm|k8s|infra)(/|$)"), "infra"),
    (re.compile(r"(^|/)(secrets?|credentials?)(/|$)|(^|/)\.env"), "secrets"),
]

# Filename hints only raise risk when the request also sounds sensitive; on their
# own they are far too common to be evidence of anything.
RISKY_NAMES = re.compile(r"(^|/)(auth|session|login|oauth|jwt|password|token|payment|billing)")
SENSITIVE_REQUEST = re.compile(
    r"\b(auth\w*|login|session|token|permission|access control|password|secret|payment|billing|"
    r"charge|refund|migrat\w+|schema|production|deploy|security|vulnerab\w+)\b", re.I,
)
# Repeated-run stability is the most expensive obligation the runtime can ask
# for: twenty clean runs of a command the agent must first identify. Live runs
# made it the commonest reason the gate fired, and on real prompts it was
# demanded of 26 percent of bug fixes, triggered by "race" and "concurrent"
# appearing inside pasted job adverts and by "sometimes" in
# "sometimes returns a string longer than the limit", which is a deterministic
# bug described conditionally.
#
# So two things are required rather than one word anywhere in the text: a term
# that actually means nondeterminism, in the same sentence as something failing.
UNAMBIGUOUS = re.compile(
    r"\b(intermittent\w*|flak\w+|heisenbug|nondeterministic|non-deterministic|"
    r"race condition|deadlock\w*|thread[- ]?saf\w+|data race)\b", re.I,
)
AMBIGUOUS = re.compile(
    r"\b(sometimes|occasionally|randomly|now and then|every so often|once in a while)\b", re.I,
)
# What turns an ambiguous adverb into a claim about nondeterminism: the same
# input behaving differently on different runs.
UNRELIABLE = re.compile(
    r"\b(not always|only sometimes|once in \w+|1 in \d+|every other run|on retry|"
    r"retrying|transient|inconsistent\w*|varies|different each|reruns?|re-runs?)\b", re.I,
)
FAILING = re.compile(
    r"\b(fail\w*|crash\w*|hang\w*|hung|error\w*|break\w*|broke\w*|bug|test\w*|"
    r"timeout\w*|times? out|stall\w*|freez\w*|flake\w*)\b", re.I,
)


def is_intermittent(request: str) -> bool:
    """Whether the bug is nondeterministic, as opposed to merely conditional.

    A term that can only mean nondeterminism stands alone, because "fix the
    intermittent race in login" says so plainly and contains no word for
    failure. An ambiguous adverb needs company: the same thing failing and not
    failing, in the same sentence as the failure itself.

    Measured on 566 real bug-fix requests, this asks for repeated runs on 4
    percent of them. The word-anywhere rule it replaces asked on 26 percent.
    """
    text = request or ""
    if UNAMBIGUOUS.search(text):
        return True
    return any(
        AMBIGUOUS.search(sentence) and UNRELIABLE.search(sentence) and FAILING.search(sentence)
        for sentence in re.split(r"[.!?\n]+", text)
    )


def risk_of(paths: list[str], request: str = "", changed_lines: int = 0) -> tuple[Risk, list[str]]:
    """Risk tier from what a task touches and what it says. No model call."""
    domains = sorted({name for p in paths for pattern, name in RISKY_DIRS if pattern.search(p)})
    if domains:
        return Risk.HIGH, domains

    if request and SENSITIVE_REQUEST.search(request) and any(RISKY_NAMES.search(p) for p in paths):
        return Risk.HIGH, ["sensitive"]

    if len(paths) > 10 or changed_lines > 300:
        return Risk.MEDIUM, []
    return (Risk.MEDIUM if len(paths) > 3 else Risk.LOW), []


def obligations_for(
    claim: Claim, risk: Risk, surface: Surface | None = None, request: str = ""
) -> list[Obligation]:
    """The obligations that apply here, filtered to what this project can prove."""
    chosen = list(TABLE[claim][risk])

    if claim is Claim.BUG_FIXED and is_intermittent(request or ""):
        chosen.append(STABLE)

    if surface is None:
        return chosen

    available = [o for o in chosen if o.available(surface)]
    if not available and claim not in (Claim.DOCS_CHANGED, Claim.CANNOT_COMPLETE):
        # Nothing this project can prove in the usual ways. Ask for the weakest
        # honest thing instead of waving the work through unchecked.
        return [RUNTIME_OK]
    return available
