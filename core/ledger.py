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

from .evidence import Evidence, Freshness, Result
from .obligations import Claim, Obligation, Risk, obligations_for

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
    evidence: list[Evidence] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    blocks: int = 0
    created: float = field(default_factory=time.time)

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

    def note(self, what: str, why: str) -> None:
        self.decisions.append({"what": what, "why": why, "at": time.time()})

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
        for obligation in obligations_for(claim, self.risk):
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
        """Currently failing evidence.

        Only the most recent record for each identity counts. A test that failed
        and was then fixed is the reproduction, not a contradiction, so a
        superseded failure must not block completion.
        """
        latest: dict[tuple, Evidence] = {}
        for e in self.evidence:
            key = (e.kind, e.identity)
            if key not in latest or e.at >= latest[key].at:
                latest[key] = e
        return [
            e for e in latest.values()
            if e.result is not Result.PASS and e.freshness(self.root) is Freshness.FRESH
        ]

    def _check(self, obligation: Obligation) -> Check:
        if obligation.require_prior_failure:
            relevant = [e for e in self.evidence if obligation.matches(e)]
            failed = [e for e in relevant if e.result is Result.FAIL]
            passed = [e for e in relevant if e.result is Result.PASS]
            met = bool(failed and passed and min(f.at for f in failed) < max(p.at for p in passed))
            return Check(obligation=obligation, met=met, evidence=failed[0] if met else None,
                         freshness=None)

        found = obligation.satisfied_by(self.evidence)
        if found is None:
            return Check(obligation=obligation, met=False)
        return Check(obligation=obligation, met=True, evidence=found, freshness=found.freshness(self.root))
