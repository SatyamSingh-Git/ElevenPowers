"""Explicit all-declared-check execution with one owner and independent receipts."""
from pathlib import Path
import subprocess
import time

from . import checks
from .jobs import Busy, Superseded, Session, current
from .ledger import Ledger

ORDER=('tests','build','typecheck','lint','benchmark')


def execute(root, *, seconds=120):
    checks.validate_seconds(seconds)
    started=time.monotonic()
    root=Path(root).resolve(strict=True)
    value={'schema_version':2,'selected':[],'results':[],'state':'incomplete','issues':[]}
    try:
        config=checks._config(root)
        selected=[p for p in ORDER if config.declares(p)]
        value['selected']=selected
        value['results']=[checks.pending(p,config.command_for(p)) for p in selected]
        if not selected:
            raise ValueError('no supported checks are declared')
        if not config.verifies:
            raise ValueError('passive off profile does not execute checks')
        if current() is not None:
            raise Busy('another verification session owns this operation')
        task=Ledger.load(root).task
        identity=checks.context(root)
        commands={p:config.command_for(p) for p in selected}
        with Session(root,task,seconds=max(0,seconds-(time.monotonic()-started))) as session:
            jobs=[session.queue('declared check '+p,commands[p]) for p in selected]
            for index,(property,job) in enumerate(zip(selected,jobs)):
                if Ledger.load(root).task!=task or checks.context(root)!=identity:
                    raise Superseded('task, configuration or producer changed during batch')
                session.budget.timeout(seconds)
                value['results'][index]=checks._execute(root,property,session,seconds=seconds,job=job)
            if Ledger.load(root).task!=task or checks.context(root)!=identity:
                raise Superseded('task, configuration or producer changed before batch closure')
    except (OSError,ValueError,Busy,Superseded,subprocess.SubprocessError) as error:
        issue=type(error).__name__+': declared batch unavailable, changed or incomplete'
        value['issues'].append(issue)
        for result in value['results']:
            if result.get('unrun'):
                result['issues']=[issue+'; not executed']
    states={r['state'] for r in value['results']}
    value['state']=('incomplete' if not states or value['issues'] or 'incomplete' in states else
                    'failed' if 'failed' in states else 'passed')
    value['elapsed_seconds']=round(time.monotonic()-started,3)
    return value
