"""The two messages that are the product's visible surface."""

from __future__ import annotations

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
