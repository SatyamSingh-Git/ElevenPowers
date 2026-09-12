"""Computing the missing evidence instead of demanding it.

Measured live, the gate blocked three quarters of runs on work that was already
correct, and in every one of those the agent had written a test and run it. What
it had not done was run the whole suite, because that is a second invocation of
the same tool and nothing does it voluntarily. Telling the agent to did not help
either: guidance at the moment of work changed the block rate by less than the
noise floor.

Blocking to make an agent run a command costs another agent turn, which is
2.5 times the tokens. Running the command is a few seconds and no tokens. When
the runtime can compute the evidence itself, demanding it is the wrong move, and
"completion is computed" is the whole thesis anyway.

Only commands the project declared are ever run. Guessing one would mean this
module executing something nobody asked for, which is not a trade worth making
for a shorter obligation list.
"""

from __future__ import annotations

import subprocess

from .evidence import Evidence
from .parsers import parse

TIMEOUT = 300


def dischargeable(ledger) -> list[str]:
    """The needs this project told us how to check, that evidence does not cover.

    Missing and stale are different reasons and the same remedy. A stale check
    stays `met=True`, so scheduling only the unmet ones meant genuinely stale
    evidence was never refreshed: the runtime could see that a result no longer
    spoke for the repository, knew the command that would settle it, and did
    nothing. Deleted inputs count too, for the same reason.
    """
    config = ledger.config
    if not config.commands:
        return []
    unmet = {
        check.obligation.needs
        for verdict in ledger.verdicts()
        for check in verdict.missing + verdict.stale
        if check.obligation.needs
    }
    return sorted(need for need in unmet if config.declares(need))


def discharge(ledger) -> list[Evidence]:
    """Run what the project declared, and record what happened.

    A failing command is recorded as faithfully as a passing one. The point is
    not to manufacture a green result, it is to find out: a suite that fails
    here turns the verdict to CONTRADICTED, which is exactly what should happen
    and what nobody would have learned by blocking.
    """
    records: list[Evidence] = []
    for need in dischargeable(ledger):
        command = ledger.config.command_for(need)
        try:
            done = subprocess.run(
                command, shell=True, cwd=ledger.root, capture_output=True,
                text=True, timeout=TIMEOUT,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        found = parse(command, (done.stdout or "") + (done.stderr or ""),
                      done.returncode, ledger.root)
        if found:
            ledger.note("ran a declared command", f"{need}: {command}")
            records.extend(found)
    return records
