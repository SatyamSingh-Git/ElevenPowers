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

from .evidence import Evidence, Freshness, Result, source_snapshot
from .jobs import Session, current, BudgetExhausted
from .process import run as run_command
from .parsers import parse, DECLARED_KINDS

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
    def reusable(need):
        from .redact import scrub
        kind = DECLARED_KINDS.get(need)
        candidates = [e for e in ledger.evidence if e.kind is kind]
        if not candidates:
            return False
        latest = max(enumerate(candidates), key=lambda pair: (pair[1].at, pair[0]))[1]
        return (latest.command_identity == scrub(config.command_for(need))
                and latest.result is Result.PASS and latest.execution == 'complete'
                and latest.ran_tests and latest.freshness(ledger.root) is Freshness.FRESH)
    # An unresolved reproduction or scoped-test obligation cannot be fixed by
    # rerunning the same successful broad command on identical inputs.
    return sorted(need for need in unmet if config.declares(need) and not reusable(need))


def discharge(ledger) -> list[Evidence]:
    """Persist each completed check before starting another one.

    An incomplete receipt is written before execution: abrupt host death must
    not leave an older success looking like the outcome of the new attempt.
    """
    if not ledger.config.verifies:
        return []
    if current() is None:
        with Session(ledger.root, ledger.task):
            return discharge(ledger)
    session = current()
    records: list[Evidence] = []
    attempted: set[str] = set()
    planned = []
    for need in dischargeable(ledger):
        command = ledger.config.command_for(need)
        if command not in attempted:
            attempted.add(command)
            planned.append((need, command, session.queue('verification', command)))
    for need, command, item in planned:
        try:
            session.budget.timeout(TIMEOUT)
        except BudgetExhausted as error:
            session.finish(item, 'deferred', str(error))
            continue
        before = source_snapshot(ledger.root, fresh=True, deadline=session.budget.deadline)
        provisional = parse(command, 'verification started; completion not yet recorded',
                            None, ledger.root, snapshot=before)
        ledger.add(provisional)
        ledger.save()
        session.begin(item)
        code, output = None, ''
        if not before[0].complete:
            output = 'input coverage incomplete; command was not launched'
        else:
            try:
                done = run_command(command, shell=True, cwd=ledger.root,
                                   timeout=session.budget.timeout(TIMEOUT))
                code = done.returncode
                output = (done.stdout or '') + (done.stderr or '')
            except subprocess.TimeoutExpired as error:
                output = _text(error.stdout) + _text(error.stderr) + '\ntimeout: command did not complete'
            except (OSError, subprocess.SubprocessError) as error:
                output = (_text(getattr(error, 'stdout', '')) + _text(getattr(error, 'stderr', ''))
                          + f'\nincomplete command: {error}')
        after = source_snapshot(ledger.root, fresh=True, deadline=session.budget.deadline)
        if before[1] != after[1] or before[0].files != after[0].files:
            before[0].issues.append('source inputs changed during verification')
        before[0].issues.extend(i for i in after[0].issues if i not in before[0].issues)
        found = parse(command, output, code, ledger.root, snapshot=before)
        ledger.add(found)
        ledger.note('ran a declared command' if code is not None else 'declared command incomplete',
                    f'{need}: {command}')
        ledger.save()
        records.extend(found)
        status = ('incomplete' if code is None else 'stale' if before[0].issues else
                  'failed' if code or any(e.result is not Result.PASS for e in found) else 'passed')
        session.finish(item, status, '; '.join(before[0].issues), exit_code=code)
    return records


def _text(value):
    return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else (value or '')
