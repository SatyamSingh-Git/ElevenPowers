"""The task ledger and the completion state computed from it.

The ledger is the external task state: which claims are open, what evidence has
been captured, and which files the task is allowed to touch. It lives on disk so
it survives compaction, resumption and a change of host.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .claims import opens_new_task
from .config import Config, load as load_config
from .evidence import Evidence, Freshness, Kind, Result
from .intent import is_abstention, is_question
from .obligations import Claim, Obligation, Risk, _demonstrated_fix, obligations_for, risk_of
from .repeat import MIN_RUNS, runs_needed
from .scope import is_manifest, is_prose, normalise
from .surface import TEST_NAME, Surface, declares_a_test, detect

STATE_DIR = ".elevenpowers"


class Status(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    CONTRADICTED = "CONTRADICTED"
    STALE = "STALE"


@dataclass
class Check:
    obligation: Obligation
    met: bool
    evidence: Evidence | None = None
    freshness: Freshness | None = None
    caveat: str = ""


@dataclass
class Verdict:
    claim: Claim
    risk: Risk
    status: Status
    checks: list[Check]

    @property
    def missing(self) -> list[Check]:
        return [c for c in self.checks if not c.met]

    @property
    def stale(self) -> list[Check]:
        """Met, but no longer speaking for the repository as it is now.

        `GONE` belongs here as much as `STALE` does. Rejecting only `STALE` left
        a claim verified by a test result whose files had been deleted — the
        strongest possible form of out of date.
        """
        return [c for c in self.checks
                if c.met and c.freshness in (Freshness.STALE, Freshness.GONE)]


@dataclass
class Ledger:
    root: Path
    task: str = ""
    request: str = ""
    claims: list[Claim] = field(default_factory=list)
    risk: Risk = Risk.LOW
    domains: list[str] = field(default_factory=list)
    touched: list[str] = field(default_factory=list)
    seen: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    blocks: int = 0
    guided: bool = False
    created: float = field(default_factory=time.time)
    _surface: Surface | None = None
    _config: Config | None = None

    @property
    def config(self) -> Config:
        if self._config is None:
            self._config = load_config(self.root)
        return self._config

    @property
    def surface(self) -> Surface:
        """What this project can prove, from a file scan plus what has been seen.

        Evidence outranks the scan: if a test command has actually produced a
        record, the project has tests whatever the layout looks like. Without
        this, an unusual directory structure silently makes every obligation
        unreachable.
        """
        if self._surface is None:
            found = detect(self.root)
            kinds = {e.kind for e in self.evidence}
            declared = self.config
            self._surface = Surface(
                tests=found.tests or bool(kinds & {Kind.TEST, Kind.SUITE}) or declared.declares("tests"),
                typecheck=found.typecheck or Kind.TYPECHECK in kinds or declared.declares("typecheck"),
                build=found.build or Kind.BUILD in kinds or declared.declares("build"),
                benchmark=found.benchmark or Kind.BENCHMARK in kinds or declared.declares("benchmark"),
            )
        return self._surface

    @property
    def path(self) -> Path:
        return self.root / STATE_DIR / "ledger.json"

    @classmethod
    def load(cls, root: Path) -> "Ledger":
        path = root / STATE_DIR / "ledger.json"
        if not path.exists():
            return cls(root=root)
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            root=root,
            task=raw.get("task", ""),
            request=raw.get("request", ""),
            claims=[Claim(c) for c in raw.get("claims", [])],
            risk=Risk(raw.get("risk", "low")),
            domains=raw.get("domains", []),
            touched=raw.get("touched", []),
            seen=raw.get("seen", []),
            evidence=[Evidence.from_dict(e) for e in raw.get("evidence", [])],
            decisions=raw.get("decisions", []),
            blocks=raw.get("blocks", 0),
            guided=raw.get("guided", False),
            created=raw.get("created", time.time()),
        )

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "task": self.task,
            "request": self.request,
            "claims": [c.value for c in self.claims],
            "risk": self.risk.value,
            "domains": self.domains,
            "touched": self.touched,
            "seen": self.seen,
            "evidence": [e.to_dict() for e in self.evidence],
            "decisions": self.decisions,
            "blocks": self.blocks,
            "guided": self.guided,
            "created": self.created,
        }
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def add(self, records: list[Evidence]) -> None:
        self.evidence.extend(records)
        self._surface = None

    def saw(self, path: str) -> None:
        """Record that the task has looked at or changed a file."""
        rel = normalise(path, self.root)
        if rel and rel not in self.seen:
            self.seen.append(rel)

    def observe_edit(self, path: str) -> None:
        """Record an edit, and open a claim if the task never stated one.

        Deriving the claim from what a task does rather than only from what was
        asked is the same move the scope guard makes, for the same reason: one
        real prompt in five is four words or fewer, and the intent for those
        lives in the conversation. A prompt that explicitly asked for something
        other than a change is left alone, so answering a question does not
        become a claim because a note was edited along the way.
        """
        rel = normalise(path, self.root)
        self.saw(rel)
        # An edit is a fact about the task whatever claim is already open.
        # Recording it only on the path that opens one meant every later edit
        # was invisible: a task that started on a README and then reached into
        # `src/auth/` kept the risk the README earned it.
        self.touched = sorted(set(self.touched) | {rel})
        self.risk, self.domains = risk_of(self.touched, self.request)
        if self.claims or not self.request or opens_new_task(self.request):
            return
        if is_manifest(rel) or is_prose(rel):
            return
        self.claims = [Claim.FEATURE_ADDED]
        self.note("claim opened by an edit", f"{rel} changed with no claim stated")

    def note(self, what: str, why: str) -> None:
        self.decisions.append({"what": what, "why": why, "at": time.time()})

    def settle(self, last_message: str = "") -> Status:
        """The completion state, given what the agent just said.

        Two readings of the final message change the answer. A question is not a
        completion claim, so gating it would force the agent to guess rather
        than wait. A stated blocker converts the task to an abstention, whose
        obligation is the reason itself, because a system with no way to accept
        "this cannot be done as asked" pushes the agent into inventing a result.
        """
        if is_question(last_message):
            return Status.VERIFIED
        if last_message and is_abstention(last_message) and self.claims:
            if self.claims != [Claim.CANNOT_COMPLETE]:
                self.claims = [Claim.CANNOT_COMPLETE]
                self.add([Evidence(
                    kind=Kind.DIFF, identity="stated-blocker", result=Result.PASS,
                    observed=[], tree="", detail=last_message.strip()[:400], at=time.time(),
                )])
        return self.status()

    def verdicts(self) -> list[Verdict]:
        return [self._verdict(claim) for claim in self.claims]

    def status(self) -> Status:
        verdicts = self.verdicts()
        if not verdicts:
            return Status.VERIFIED
        order = [Status.CONTRADICTED, Status.UNVERIFIED, Status.STALE, Status.VERIFIED]
        return min((v.status for v in verdicts), key=order.index)

    def _verdict(self, claim: Claim) -> Verdict:
        checks: list[Check] = []
        for obligation in obligations_for(claim, self.risk, self.surface, self.request):
            checks.append(self._check(obligation))

        if self._contradictions():
            status = Status.CONTRADICTED
        elif any(not c.met for c in checks):
            status = Status.UNVERIFIED
        elif any(c.freshness in (Freshness.STALE, Freshness.GONE) for c in checks):
            status = Status.STALE
        else:
            status = Status.VERIFIED
        return Verdict(claim=claim, risk=self.risk, status=status, checks=checks)

    def _contradictions(self) -> list[Evidence]:
        """Evidence that is failing now and was not already failing at the start.

        Two rules, both learned by measurement. Only the most recent record for
        an identity counts, so a test that failed and was then fixed reads as
        reproduction rather than contradiction. And an identity whose first
        observation in this task was already failing is pre-existing breakage:
        plenty of real repositories have a red test on the main branch, and
        blaming the agent for it blocks every task on such a repository.
        """
        first: dict[tuple, Evidence] = {}
        latest: dict[tuple, Evidence] = {}
        for e in self.evidence:
            key = (e.kind, e.identity)
            if key not in first or e.at < first[key].at:
                first[key] = e
            if key not in latest or e.at >= latest[key].at:
                latest[key] = e
        return [
            e for key, e in latest.items()
            if e.result is not Result.PASS
            and first[key].result is Result.PASS
            and e.freshness(self.root) is Freshness.FRESH
        ]

    def pre_existing(self) -> list[Evidence]:
        """Failures that were already there when the task started.

        Stability measurements are excluded: a repeat run that found the bug is
        the reproduction the task exists to fix, not somebody else's breakage.
        """
        first: dict[tuple, Evidence] = {}
        for e in self.evidence:
            if e.kind is Kind.STABILITY:
                continue
            key = (e.kind, e.identity)
            if key not in first or e.at < first[key].at:
                first[key] = e
        return [e for e in first.values() if e.result is not Result.PASS]

    def _check(self, obligation: Obligation) -> Check:
        if obligation.require_prior_failure:
            relevant = [e for e in self.evidence if obligation.matches(e)]
            failed = [e for e in relevant if e.result is Result.FAIL]
            passed = [e for e in relevant if e.result is Result.PASS]
            if failed and passed and min(f.at for f in failed) < max(p.at for p in passed):
                return Check(obligation=obligation, met=True, evidence=failed[0])
            # Where tests only run through an opaque wrapper there is no scoped
            # record to point at, but a target going from red to green is the
            # reproduction by any other name.
            shown = _demonstrated_fix(self.evidence)
            return Check(obligation=obligation, met=shown is not None, evidence=shown)

        if obligation.kind is Kind.STABILITY:
            return self._check_stability(obligation)

        found = obligation.satisfied_by(self.evidence)
        if found is not None:
            return Check(obligation=obligation, met=True, evidence=found,
                         freshness=found.freshness(self.root))

        written = self._test_written_and_suite_green(obligation)
        if written is not None:
            return Check(obligation=obligation, met=True, evidence=written,
                         freshness=written.freshness(self.root),
                         caveat="a test was written and the suite that runs it passed")

        tolerated = self._no_new_failures(obligation)
        if tolerated is not None:
            return Check(obligation=obligation, met=True, evidence=tolerated,
                         freshness=tolerated.freshness(self.root), caveat="no new failures")
        return Check(obligation=obligation, met=False)

    def required_runs(self) -> int:
        """How many clean runs would justify calling an intermittent bug fixed.

        Derived from the worst failure rate this task actually observed, so the
        answer is arithmetic rather than a guess. With nothing observed, fall
        back to the floor and say so.
        """
        rates = [
            e.failed / e.runs
            for e in self.evidence
            if e.kind is Kind.STABILITY and e.runs and e.failed
        ]
        return runs_needed(max(rates)) if rates else MIN_RUNS

    def _check_stability(self, obligation: Obligation) -> Check:
        """Stability needs enough clean repeats, not one lucky run.

        A single successful execution is indistinguishable from a hundred of
        them unless something counted, so this is the one obligation that
        requires its own tool.
        """
        records = [e for e in self.evidence if e.kind is Kind.STABILITY]
        if not records:
            return Check(obligation=obligation, met=False)

        needed = self.required_runs()
        clean = [e for e in records if e.failed == 0 and e.runs >= needed]
        if clean:
            best = max(clean, key=lambda e: e.runs)
            return Check(obligation=obligation, met=True, evidence=best,
                         freshness=best.freshness(self.root))

        best = max(records, key=lambda e: (e.failed == 0, e.runs))
        short = best.failed == 0 and best.runs < needed
        return Check(
            obligation=obligation, met=False, evidence=best,
            caveat=(f"{best.runs} clean runs, {needed} needed" if short
                    else f"still failed {best.failed} of {best.runs}"),
        )

    def _test_written_and_suite_green(self, obligation: Obligation) -> Evidence | None:
        """This task wrote a test, and the suite that contains it passed.

        A whole-suite run produces no per-test record, so an agent that writes a
        covering test and then runs everything cannot discharge a scoped
        obligation. That described three quarters of the runs the gate blocked
        in live measurement, in every one of which a test file had been edited.

        Watching the task write a test and the suite go green is the same proof
        by a different route, which is the argument that already admits a
        red-to-green transition. It is weaker than a named passing test, so it
        is reported with the caveat rather than silently.
        """
        if not obligation.scoped or obligation.kind is not Kind.TEST:
            return None
        # Written, not read. `seen` includes files the agent merely opened, so
        # reading an existing test and running a green suite satisfied "a test
        # covering the change passes" — with a caveat that said a test had been
        # written. Nuisance blocking is not a reason to upgrade weaker evidence
        # into a stronger claim.
        #
        # The file must also still declare a test. Emptying one is how a suite
        # goes green without the bug being fixed, and the held-out scenarios
        # caught exactly that the first time this rule was written without it.
        if not any(TEST_NAME.search(p) and declares_a_test(self.root / p)
                   for p in self.touched):
            return None
        green = [
            e for e in self.evidence
            if e.kind is Kind.SUITE and e.result is Result.PASS and e.ran_tests
            and not Obligation._is_scoped(e)
        ]
        return green[-1] if green else None

    def _no_new_failures(self, obligation: Obligation) -> Evidence | None:
        """A suite that was already red and is no redder than before.

        Some repositories are red on their main branch. Demanding a green suite
        there makes every task impossible, so the standard becomes the one the
        agent can actually meet: introduce no new failures. This mirrors the
        way linters are applied to agent edits, counting only errors the change
        itself added.
        """
        if not obligation.broad:
            return None
        runs = [e for e in self.evidence if obligation.matches(e)]
        if len(runs) < 2:
            return None
        runs.sort(key=lambda e: e.at)
        first, last = runs[0], runs[-1]
        if first.result is Result.PASS or last.result is Result.PASS:
            return None
        # Which tests failed, not how many. A suite that swapped an old failure
        # for a new one keeps its count and has regressed, and counting alone
        # cannot tell those apart. Where the runner reported no per-test detail
        # there is nothing to compare, and the concession is refused rather than
        # granted on a number that cannot support it.
        was, now = self._failing_tests(first.at), self._failing_tests(last.at)
        if not was or not now or now - was:
            return None
        return last if last.failed <= first.failed else None

    def _failing_tests(self, when: float) -> set[str]:
        """The tests a single suite run reported failing, by name.

        Per-test records share the timestamp of the run that produced them,
        which is what ties them to one invocation rather than to the task.
        """
        return {e.identity for e in self.evidence
                if e.kind is Kind.TEST and e.result is not Result.PASS and e.at == when}
