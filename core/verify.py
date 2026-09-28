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

Commands come from explicit project overrides or supported root manifest
conventions. Missing obligations decide what runs; discovery itself executes
nothing, and the passive profile does not invoke this path.
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
    attempted: set[str] = set()
    for need in dischargeable(ledger):
        command = ledger.config.command_for(need)
        if command in attempted:
            continue
        attempted.add(command)
        try:
            done = subprocess.run(
                command, shell=True, cwd=ledger.root, capture_output=True,
                text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT,
            )
        except subprocess.TimeoutExpired as error:
            def text(value):
                return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else (value or "")
            output = text(error.stdout) + text(error.stderr) + "\ntimeout: command did not complete"
            records.extend(parse(command, output, None, ledger.root))
            ledger.note("declared command incomplete", f"timeout: {command}")
            continue
        except (OSError, subprocess.SubprocessError) as error:
            records.extend(parse(command, f"launch error: {error}", None, ledger.root))
            ledger.note("declared command incomplete", f"launch error: {command}")
            continue
        found = parse(command, (done.stdout or "") + (done.stderr or ""),
                      done.returncode, ledger.root)
        if found:
            ledger.note("ran a declared command", f"{need}: {command}")
            records.extend(found)
    return records
