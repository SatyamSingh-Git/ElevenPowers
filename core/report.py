"""The two messages that are the product's visible surface."""

from __future__ import annotations

import re

from .atlas import reflexion, since
from .atlas import wording as drift_wording
from .evidence import Freshness, Kind, Result
from .ledger import Ledger, Status, Verdict
from .ratchet import offer
from .stress import wording

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
                lines.append(f"           {_hint(ledger, check)}")
                if check.caveat:
                    lines.append(f"           so far: {check.caveat}")
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


def guidance(ledger: Ledger) -> str:
    """What would prove this work, said while there is still time to do it.

    The gate speaks at the end, by which point the obligations named in the
    opening banner are far behind. Measured live, it stopped nearly every first
    attempt to finish, and nearly always on work that was already correct: the
    agent had done the job and simply not shown it. This is the same
    information delivered at the moment it can still change what happens, which
    is the difference between a reminder and an interruption.
    """
    missing = [c for v in ledger.verdicts() for c in v.missing]
    if not missing:
        return ""
    lines = ["this task will need, before it can be called done:"]
    for check in missing:
        lines.append(f"  {check.obligation.description}")
        lines.append(f"    {_hint(ledger, check)}")
    return "\n".join(lines)


def _hint(ledger: Ledger, check) -> str:
    """The hint, made specific where the runtime can compute the specifics."""
    if check.obligation.kind is not Kind.STABILITY:
        # A command the project declared beats one this module guessed at, and
        # guessing produced hints naming commands that did not exist.
        declared = ledger.config.command_for(check.obligation.needs)
        return f"run: {declared}" if declared else check.obligation.hint
    needed = ledger.required_runs()

    # Whatever was already measured for flakiness is by definition the command
    # that shows the bug, so repeat that one rather than guessing again.
    measured = [e for e in ledger.evidence if e.kind is Kind.STABILITY and e.identity]
    if measured:
        return f"ep-repeat {needed} -- {measured[-1].identity}"

    ran = [e for e in ledger.evidence
           if e.kind in (Kind.TEST, Kind.SUITE, Kind.RUNTIME) and e.command]
    failed_once = {e.identity for e in ran if e.result is not Result.PASS}
    candidates = [e for e in ran if e.identity in failed_once] or ran
    command = candidates[-1].command if candidates else "<the command that reproduced it>"
    return f"ep-repeat {needed} -- {command}"


def coverage_note(ledger: Ledger) -> str:
    """Point at a test that looks more related than the one that was run.

    Deliberately advisory, and deliberately quiet. Deciding coverage properly
    needs a test-to-source map; naming alone would flag every project whose
    tests are named differently from the code they exercise, which is most of
    them. So this speaks only when a better-matching test file exists and was
    not the one run, which is the case where the reader can act on it.
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
    if not changed:
        return ""
    ran = {r.identity for r in scoped}
    if any(changed & _tokens(name) for name in ran):
        return ""

    better = [
        path for path in _test_files(ledger.root)
        if changed & _tokens(path) and not any(path in name for name in ran)
    ]
    if not better:
        return ""
    return (f"note: {', '.join(sorted(better)[:3])} looks closer to what you changed "
            f"than {', '.join(sorted(ran))}")


# Data and configuration living under `tests/`. `TEST_NAME` matches the
# directory, so attrs' `tests/test_mypy.yml` came back as the test to run, and
# `tests/__init__.py` came back as the closest cover for eight callers. Neither
# can be run, and naming an unrunnable file is worse than naming none.
NOT_RUNNABLE = re.compile(r"\.(ya?ml|json|toml|cfg|ini|txt|md|rst|lock)$|(^|/)__init__\.py$")


def _test_files(root) -> list[str]:
    from .surface import TEST_NAME, _walk

    return [p for p in _walk(root) if TEST_NAME.search(p) and not NOT_RUNNABLE.search(p)]


def _tokens(path: str) -> set[str]:
    stem = re.split(r"[/\\]", path)[-1]
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
                if check.evidence.kind is Kind.STABILITY:
                    counts = f" {check.evidence.runs} runs, {check.evidence.failed} failed"
                elif check.evidence.passed or check.evidence.failed:
                    counts = f" {check.evidence.passed} passed, {check.evidence.failed} failed"
                detail = f"  <- {check.evidence.identity}{counts}"
            lines.append(f"    {state:<8}{check.obligation.description}{detail}")
            # What an obligation was met *at* can matter as much as that it was
            # met. A reproduction established only at suite grain is the same
            # base-tree run that decided discrimination, and printing the two
            # as separate green lines says more than was established.
            if check.caveat:
                lines.append(f"             {check.caveat}")
    captured = len(ledger.evidence)
    fresh = sum(1 for e in ledger.evidence if e.freshness(ledger.root) is Freshness.FRESH)
    lines.append(f"  evidence: {captured} record(s), {fresh} fresh")
    pre = ledger.pre_existing()
    if pre:
        lines.append("  pre-existing failures, not attributed to this change: "
                     + ", ".join(e.identity for e in pre))
    # A check that could not have failed is worth saying out loud even when the
    # verdict is green, because a green verdict resting on one is the failure
    # this whole layer exists to prevent.
    for said in wording(ledger.discrimination):
        lines.append(f"  could not fail: {said}")
    # A state that was proven and has since been moved off is worth naming even
    # when the current verdict is green: the point of 5.6 is that the latest
    # patch is not automatically the best one.
    proven = offer(ledger.root, ledger.task)
    if proven:
        lines.append("  " + proven.replace("\n", "\n  "))
    note = coverage_note(ledger)
    if note:
        lines.append(f"  {note}")
    # The map and the docs, against the code. Report-only: naming what went
    # stale is useful even if it never refuses anything, and the false-positive
    # rate has not been measured on real repositories yet.
    for said in drift_wording(reflexion(ledger.root, *since(ledger.root, ledger.base))):
        lines.append(f"  {said}")
    return "\n".join(lines)
