"""What the runtime currently believes, on demand.

Until now the only way to find out was to finish a turn and be told. A
verification layer whose state can only be observed by tripping over it is one
the user cannot reason about, and everything it knows is already on disk.
"""

from __future__ import annotations

from pathlib import Path

from . import blindspots
from .evidence import Freshness
from .ledger import Ledger, Status
from .report import _hint


def render(root: Path) -> str:
    ledger = Ledger.load(root)
    config = ledger.config
    lines = [f"profile   {config.profile}"]
    if config.commands:
        for need, command in sorted(config.commands.items()):
            lines.append(f"          {need}: {command}")

    if not ledger.claims:
        lines.append("claims    none, so the runtime is standing aside")
        return "\n".join(lines + _evidence_lines(ledger) + _blindspot_lines(root))

    lines.append(f"task      {ledger.request[:70] or '(none recorded)'}")
    lines.append(f"claims    {', '.join(c.value for c in ledger.claims)}")
    domains = f" [{', '.join(ledger.domains)}]" if ledger.domains else ""
    lines.append(f"risk      {ledger.risk.value}{domains}")

    status = ledger.status()
    lines.append(f"state     {status.value}"
                 + ("" if status is Status.VERIFIED else "  (would not pass the gate)"))
    for verdict in ledger.verdicts():
        for check in verdict.checks:
            if check.met and check.freshness is Freshness.STALE:
                mark, extra = "stale  ", f"  <- {check.evidence.identity}"
            elif check.met:
                mark = "met    "
                extra = f"  <- {check.evidence.identity}" if check.evidence else ""
            else:
                mark, extra = "missing", ""
            lines.append(f"  {mark} {check.obligation.description}{extra}")
            if not check.met:
                lines.append(f"          {_hint(ledger, check)}")

    return "\n".join(lines + _evidence_lines(ledger) + _blindspot_lines(root))


def _evidence_lines(ledger: Ledger) -> list[str]:
    if not ledger.evidence:
        return ["evidence  none captured yet"]
    fresh = sum(1 for e in ledger.evidence if e.freshness(ledger.root) is Freshness.FRESH)
    out = [f"evidence  {len(ledger.evidence)} record(s), {fresh} fresh"]
    for record in ledger.evidence[-3:]:
        out.append(f"          {record.kind.value:<10} {record.result.value:<5} {record.identity}")
    return out


def _blindspot_lines(root: Path) -> list[str]:
    found = blindspots.read(root)
    if not found:
        return []
    return [f"blind     {len(found)} unreadable payload(s); run ep-doctor"]
