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

from .evidence import Evidence, Freshness, Kind, Result
from .intent import is_abstention, is_question
from .obligations import Claim, Obligation, Risk, _demonstrated_fix, obligations_for
from .surface import Surface, detect

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
        return [c for c in self.checks if c.met and c.freshness is Freshness.STALE]


@dataclass
class Ledger:
    root: Path
    task: str = ""
    request: str = ""
    claims: list[Claim] = field(default_factory=list)
    risk: Risk = Risk.LOW
    domains: list[str] = field(default_factory=list)
    allow: list[str] = field(default_factory=list)
    touched: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    blocks: int = 0
    created: float = field(default_factory=time.time)
    _surface: Surface | None = None

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
            self._surface = Surface(
                tests=found.tests or bool(kinds & {Kind.TEST, Kind.SUITE}),
                typecheck=found.typecheck or Kind.TYPECHECK in kinds,
                build=found.build or Kind.BUILD in kinds,
                benchmark=found.benchmark or Kind.BENCHMARK in kinds,
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
            allow=raw.get("allow", []),
            touched=raw.get("touched", []),
            evidence=[Evidence.from_dict(e) for e in raw.get("evidence", [])],
            decisions=raw.get("decisions", []),
            blocks=raw.get("blocks", 0),
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
            "allow": self.allow,
            "touched": self.touched,
            "evidence": [e.to_dict() for e in self.evidence],
            "decisions": self.decisions,
            "blocks": self.blocks,
            "created": self.created,
        }
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def add(self, records: list[Evidence]) -> None:
        self.evidence.extend(records)
        self._surface = None

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
        elif any(c.freshness is Freshness.STALE for c in checks):
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
        """Failures that were already there when the task started."""
        first: dict[tuple, Evidence] = {}
        for e in self.evidence:
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

        found = obligation.satisfied_by(self.evidence)
        if found is not None:
            return Check(obligation=obligation, met=True, evidence=found,
                         freshness=found.freshness(self.root))

        tolerated = self._no_new_failures(obligation)
        if tolerated is not None:
            return Check(obligation=obligation, met=True, evidence=tolerated,
                         freshness=tolerated.freshness(self.root), caveat="no new failures")
        return Check(obligation=obligation, met=False)

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
        return last if last.failed <= first.failed else None
