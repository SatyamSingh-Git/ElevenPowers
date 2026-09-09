"""The two messages that are the product's visible surface."""

from __future__ import annotations

import re

from .evidence import Freshness
from .ledger import Ledger, Status, Verdict

MARK = {True: "met     ", False: "missing "}


def gate_message(ledger: Ledger) -> str:
    """What the agent is told when the gate blocks. Specific, not scolding."""
    lines: list[str] = []
    for verdict in ledger.verdicts():
        if verdict.status is Status.VERIFIED:
            continue
        lines.append(f"{verdict.status.value}  {verdict.claim.value}")
        for check in verdict.checks:
            if check.met and check.freshness is Freshness.STALE:
                lines.append(f"  stale    {check.obligation.description}")
                lines.append(f"           recorded at tree {check.evidence.tree}, files have changed since")
                lines.append(f"           re-run: {check.evidence.command}")
            elif check.met:
                lines.append(f"  met      {check.obligation.description}")
            else:
                lines.append(f"  missing  {check.obligation.description}")
                lines.append(f"           {check.obligation.hint}")
    if not lines:
        return ""
    lines.append("")
    lines.append("Discharge the missing obligations, or record cannot_complete with a reason.")
    return "\n".join(lines)


def start_banner(ledger: Ledger) -> str:
    claims = ", ".join(c.value for c in ledger.claims) or "none inferred"
    domains = f" [{', '.join(ledger.domains)}]" if ledger.domains else ""
    obligations = sum(len(v.checks) for v in ledger.verdicts())
    return (
        f"claims: {claims}\n"
        f"risk:   {ledger.risk.value}{domains}\n"
        f"proof:  {obligations} obligation(s) to discharge"
    )


def coverage_note(ledger: Ledger) -> str:
    """Warn when the covering test looks unrelated to what changed.

    Deliberately advisory. Deciding this properly needs a test-to-source map;
    guessing from names would block correct work whenever a test is named
    differently from the code it exercises, and a false block costs more than a
    missed warning.
    """
    if not ledger.touched:
        return ""
    scoped = [
        c.evidence for v in ledger.verdicts() for c in v.checks
        if c.met and c.evidence and c.obligation.scoped
    ]
    if not scoped:
        return ""
    changed = {t for p in ledger.touched for t in _tokens(p)}
    for record in scoped:
        if changed & _tokens(record.identity):
            return ""
    names = ", ".join(sorted({r.identity for r in scoped}))
    return f"note: {names} shares no name with the files you changed; confirm it covers them"


def _tokens(path: str) -> set[str]:
    stem = re.split(r"[/\]", path)[-1]
    stem = re.sub(r"\.[A-Za-z0-9]+$", "", stem)
    parts = re.split(r"[^A-Za-z0-9]+|(?<=[a-z])(?=[A-Z])", stem)
    return {p.lower() for p in parts if len(p) > 2 and p.lower() not in
            {"test", "tests", "spec", "specs"}}


def end_report(ledger: Ledger) -> str:
    status = ledger.status()
    lines = [f"{status.value}"]
    for verdict in ledger.verdicts():
        lines.append(f"  {verdict.claim.value} ({verdict.status.value.lower()})")
        for check in verdict.checks:
            state = "ok" if check.met and check.freshness is not Freshness.STALE else (
                "stale" if check.met else "missing"
            )
            detail = ""
            if check.evidence:
                counts = ""
                if check.evidence.passed or check.evidence.failed:
                    counts = f" {check.evidence.passed} passed, {check.evidence.failed} failed"
                detail = f"  <- {check.evidence.identity}{counts}"
            lines.append(f"    {state:<8}{check.obligation.description}{detail}")
    captured = len(ledger.evidence)
    fresh = sum(1 for e in ledger.evidence if e.freshness(ledger.root) is Freshness.FRESH)
    lines.append(f"  evidence: {captured} record(s), {fresh} fresh")
    return "\n".join(lines)
