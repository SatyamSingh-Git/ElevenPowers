"""Read exact declared-check state without changing completion semantics."""
from __future__ import annotations

from dataclasses import dataclass

from .evidence import Freshness, Kind, Result
from .parsers import DECLARED_KINDS
from .redact import scrub


STATES = ("CURRENT", "FAILED", "STALE", "ABSENT", "INCOMPLETE")


@dataclass(frozen=True)
class DeclaredCheck:
    """The newest exact receipt for one configured project declaration."""

    declaration: str
    kind: Kind
    state: str
    result: str = ""
    execution: str = ""
    freshness: str = ""


def _state(record, root):
    if record.execution != "complete":
        return "INCOMPLETE", "", record.execution, ""
    if record.kind is Kind.SUITE and not record.ran_tests:
        return "INCOMPLETE", record.result.value, record.execution, ""
    freshness = record.freshness(root)
    if freshness is not Freshness.FRESH:
        return "STALE", record.result.value, record.execution, freshness.value
    if record.result is not Result.PASS or record.failed:
        return "FAILED", record.result.value, record.execution, freshness.value
    return "CURRENT", record.result.value, record.execution, freshness.value


def rows(ledger) -> list[DeclaredCheck]:
    """Classify each configured supported declaration from exact receipts only."""
    value = []
    for declaration, kind in DECLARED_KINDS.items():
        command = ledger.config.command_for(declaration)
        if not command:
            continue
        matches = [record for record in ledger.evidence
                   if record.declaration == declaration and record.kind is kind
                   and record.command_identity == scrub(command)]
        if not matches:
            value.append(DeclaredCheck(declaration, kind, "ABSENT"))
            continue
        latest = max(matches, key=lambda record: record.at)
        state, result, execution, freshness = _state(latest, ledger.root)
        value.append(DeclaredCheck(declaration, kind, state, result, execution, freshness))
    return value


def lines(ledger) -> list[str]:
    """Compact informational completion text; it never changes the verdict."""
    value = rows(ledger)
    if not value:
        return []
    output = ["Declared checks (informational; does not change the task verdict or run commands):"]
    for row in value:
        detail = "no exact receipt" if row.state == "ABSENT" else ", ".join(
            part for part in (row.result, row.execution, row.freshness) if part
        )
        output.append(f"  {row.state:<11}{row.declaration}" + (f" ({detail})" if detail else ""))
    return output
