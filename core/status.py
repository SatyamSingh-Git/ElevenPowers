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
        return "\n".join(lines + _assumption_lines(ledger) + _evidence_lines(ledger) + _blindspot_lines(root))

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

    return "\n".join(lines + _assumption_lines(ledger) + _evidence_lines(ledger) + _blindspot_lines(root))


def _assumption_lines(ledger: Ledger) -> list[str]:
    """Patterns nothing you ran produced, available while you can still act.

    **Pulled, never pushed, and that is a measured decision rather than a
    stylistic one.** The same information is reported at the proposed stop,
    which by this project's own figures is far too late - the median decisive
    error lands at step 7 of 27 and the recovery window is one step. The obvious
    remedy is to inject it into the loop the moment a command runs.

    The evidence says do not. A critic with **AUROC 0.94** - excellent detection
    - caused a **26 percentage point collapse** when it was allowed to intervene,
    helping only on task sets that were already failing and harming ones that
    were succeeding (*Accurate Failure Prediction in Agents Does Not Imply
    Effective Failure Prevention*, arXiv:2602.03338). Its authors' conclusion is
    that the value of such a framework is "identifying when **not** to
    intervene", and that a 50-task pilot is needed before trusting one.

    This project has paid that bill once already, blocking 75% of runs on a
    signal it had not measured. So the information sits here, where an agent or
    a person can ask for it at step 7 without anything being injected into a
    trajectory that may be going perfectly well. §5.12: detection and
    intervention are separately justified.
    """
    from .assumptions import unverified, vacuous_tests

    patterns = unverified(ledger)
    vacuous = vacuous_tests(ledger)
    if not patterns and not vacuous:
        return []
    lines = ["unchecked"]
    for body in patterns[:3]:
        lines.append(f"          pattern {body[:56]!r} matched nothing you ran")
    if len(patterns) > 3:
        lines.append(f"          ...and {len(patterns) - 3} more")
    for path in vacuous[:3]:
        lines.append(f"          {path} passed on the tree as it was")
    return lines


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
