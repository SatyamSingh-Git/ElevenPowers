"""Explicit exact project checks, using the existing owned process/receipt runtime."""
import math
from pathlib import Path
import subprocess
import sys
import time
import uuid

from .config import load
from .evidence import source_snapshot, Result
from .inputs import execution as inputs
from .inputs.native import configuration, digest
from .inputs.receipts import hexadecimal
from .jobs import Session, Busy, Superseded, current
from .ledger import Ledger
from .parsers import parse, DECLARED_KINDS
from .redact import scrub


def context(root):
    from .hosts.provenance import fingerprint
    return {'configuration': configuration(root), 'producer': fingerprint()}


def valid(value):
    return (isinstance(value, dict) and set(value) - {'issues'} == {'schema', 'attempt', 'configuration', 'producer'}
            and type(value['schema']) is int and value['schema'] == 1
            and isinstance(value.get('issues', []), list) and len(value.get('issues', [])) <= 16
            and all(isinstance(i, str) and len(i) <= 256 for i in value.get('issues', []))
            and all(hexadecimal(value[k]) for k in ('attempt', 'configuration', 'producer')))


def bound(value, root):
    if not valid(value) or value.get('issues'):
        return False
    try:
        return context(root) == {k: value[k] for k in ('configuration', 'producer')}
    except (OSError, ValueError, TimeoutError):
        return False


def inspect(value, root):
    state = 'not_configured' if value == {} else 'bound' if bound(value, root) else 'incomplete'
    return {'state': state, 'issues': [] if state != 'incomplete' else
            ['Owned command configuration/producer association changed or is incomplete.']}


def _config(root):
    # The ordinary loader is intentionally tolerant. Explicit execution refuses
    # a damaged saved declaration instead of running discovered fallback text.
    from .inputs.definition import raw, decode
    data = raw(root / '.elevenpowers/config.json', 1024 * 1024, optional=True)
    if data is not None:
        value = decode(data)
        if (not isinstance(value, dict) or not isinstance(value.get('commands', {}), dict)
                or any(not isinstance(v, str) for v in value.get('commands', {}).values())):
            raise ValueError('invalid saved command configuration')
        from .health import _configuration
        return _configuration(root)
    return load(root)


def available(root):
    root = Path(root).resolve(strict=True)
    config = _config(root)
    return {'schema_version': 1, 'profile': config.profile,
            'commands': {k: scrub(v) for k, v in sorted(config.commands.items()) if k in DECLARED_KINDS}}


def guidance(root, *, commands=None, batch=False):
    """Executable host-shell-neutral entry point; inspection never launches it."""
    from .hosts.setup import invocation
    root = Path(root).resolve(strict=True)
    config = _config(root)
    properties = [k for k, v in config.commands.items() if k in DECLARED_KINDS
                  and (commands is None or v in commands)]
    if not properties or not config.verifies:
        return ''
    ordered=sorted(properties,key=lambda p:(p!='tests',p));lines=[];shown=[]
    if batch and commands is None:
        import json
        args=[sys.executable,str(Path(__file__).resolve().parents[1]/'plugin/bin/ep_check.py'),
              '--all','--project',str(root)]
        message=('Owned check arguments: '+json.dumps(args,ensure_ascii=True)+'\n'
                 +'Owned declared checks ('+', '.join(ordered)+'): '+invocation(args))
        # Leave room for the native prompt's brief receipt explanation.
        if len(message)<=1930:
            return message
        return ('Owned batch instructions not shown for '+', '.join(ordered)
                +': invocation exceeds the context bound. Inspect ep_check.py --list; no check is verified by this advice.')
    for selected in ordered:
        line = f'Owned declared check {selected}: ' + invocation([
            sys.executable, str(Path(__file__).resolve().parents[1] / 'plugin/bin/ep_check.py'),
            selected, '--project', str(root)])
        # Reserve room to name any command instructions omitted by the bound.
        if len('\n'.join([*lines,line]))<=1680:
            lines.append(line);shown.append(selected)
    missing=[p for p in ordered if p not in shown]
    if missing:
        lines.append('Additional declared check instructions not shown: '+', '.join(missing)+
                     '. Inspect ep_check.py --list; these checks are not verified by another property passing.')
    return '\n'.join(lines)


def validate_seconds(seconds):
    if type(seconds) not in (int, float) or not 0 < seconds <= 600 or not math.isfinite(seconds):
        raise ValueError('seconds must be finite, positive and at most 600')


def pending(property, command='', *, issue='not executed'):
    return {'schema_version': 1, 'state': 'incomplete', 'property': property,
            'command': scrub(command), 'exit_code': None, 'issues': [issue],
            'receipt_count': 0, 'attempt': None, 'unrun': True, 'elapsed_seconds': 0}


def execute(root, property, *, seconds=120):
    """Run one selected check under its own project owner and total deadline."""
    validate_seconds(seconds)
    started = time.monotonic()
    root = Path(root).resolve(strict=True)
    result = pending(property)
    try:
        config = _config(root)
        if property not in DECLARED_KINDS or not config.declares(property):
            raise ValueError('selected property has no supported declared command')
        if not config.verifies:
            raise ValueError('passive off profile does not execute checks')
        if current() is not None:
            raise Busy('another verification session owns this operation')
        with Session(root, Ledger.load(root).task, seconds=max(0, seconds-(time.monotonic()-started))) as session:
            result = _execute(root, property, session, seconds=seconds)
    except (OSError, ValueError, Busy, Superseded, subprocess.SubprocessError) as error:
        result['issues'].append(type(error).__name__ + ': declared check unavailable or incomplete')
    result['elapsed_seconds'] = round(time.monotonic()-started, 3)
    return result


def _execute(root, property, session, *, seconds, job=None):
    """The same qualified child path, using an already held single or batch owner."""
    started = time.monotonic()
    result = {'schema_version': 1, 'state': 'incomplete', 'property': property,
              'command': '', 'exit_code': None, 'issues': [], 'receipt_count': 0,
              'attempt': digest(uuid.uuid4().hex), 'unrun': True}
    try:
        if current() is not session or session.root.resolve() != root.resolve():
            raise Busy('the supplied project owner is not active')
        config = _config(root)
        if property not in DECLARED_KINDS or not config.declares(property) or not config.verifies:
            raise ValueError('selected check is unavailable or passive')
        command = config.command_for(property)
        result['command'] = scrub(command)
        ledger = Ledger.load(root)
        if ledger.task != session.task:
            raise Superseded('task changed before ownership')
        before_context = context(root)
        if _config(root).command_for(property) != command or not _config(root).verifies:
            raise ValueError('declared command or profile changed before launch')
        snapshot = source_snapshot(root, fresh=True, deadline=session.budget.deadline)
        observed = inputs.begin(root, session.budget.deadline, command=command, declared=True)
        binding = {'schema': 1, 'attempt': result['attempt'], **before_context}
        provisional = parse(command, 'declared check started; completion not recorded', None, root, snapshot=snapshot)
        for record in provisional:
            record.owned_execution = binding
        inputs.provisional(provisional, observed)
        ledger.add(provisional); ledger.save(expected_task=session.task)
        job = job or session.queue('declared check', command)
        session.begin(job)
        issues = list(snapshot[0].issues)
        code, output = None, ''
        if not snapshot[0].complete or not inputs.ready(observed):
            issues.append('input coverage is incomplete; command was not launched')
        else:
            try:
                if context(root) != before_context or Ledger.load(root).task != session.task:
                    raise ValueError('execution context changed before launch')
                allowance = session.budget.timeout(seconds)
                result['unrun'] = False
                done = _run(command, root, allowance)
                code, output = done.returncode, (done.stdout or '') + (done.stderr or '')
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                issues.append(type(error).__name__ + ': declared check did not complete')
                output = _text(getattr(error, 'stdout', '')) + _text(getattr(error, 'stderr', ''))
        result['exit_code'] = code
        after = source_snapshot(root, fresh=True, deadline=session.budget.deadline)
        source_issues = list(after[0].issues)
        if after[1] != snapshot[1] or after[0].files != snapshot[0].files:
            source_issues.append('source inputs changed during declared check')
        issues.extend(source_issues)
        if context(root) != before_context:
            issues.append('configuration or producer changed during declared check')
            binding = {**binding, 'issues': ['configuration or producer changed during declared check']}
        if Ledger.load(root).task != session.task:
            raise Superseded('task changed during declared check; provisional evidence retained')
        snapshot[0].issues.extend(i for i in source_issues if i not in snapshot[0].issues)
        records = parse(command, output, code, root, snapshot=snapshot)
        for record in records:
            record.owned_execution = binding
        inputs.finish(root, session.budget.deadline, observed, records, issues)
        ledger.add(records); ledger.save(expected_task=session.task)
        aggregates = [e for e in records if e.declaration == property and e.kind is DECLARED_KINDS[property]]
        input_gap = any(e.external_inputs and e.external_inputs.get('state') != 'bound' for e in records)
        state = ('incomplete' if code is None or issues or input_gap or not aggregates else
                 'failed' if code or any(e.result is not Result.PASS for e in aggregates) else
                 'incomplete' if any(not e.ran_tests for e in aggregates) else 'passed')
        result.update(state=state, receipt_count=len(records), issues=list(dict.fromkeys(issues)))
        if input_gap:
            result['issues'].append('selected external input association is incomplete')
        session.finish(job, state, exit_code=code)
    except (OSError, ValueError, Busy, Superseded, subprocess.SubprocessError) as error:
        result['issues'].append(type(error).__name__ + ': declared check unavailable or incomplete')
        if job is not None and job.get('status') in ('queued', 'running'):
            session.finish(job, 'incomplete', type(error).__name__)
    result['elapsed_seconds'] = round(time.monotonic()-started, 3)
    return result


def _run(command, root, seconds):
    from .process import run
    return run(command, cwd=root, timeout=seconds, shell=True)


def _text(value):
    return value.decode('utf8', errors='replace') if isinstance(value, bytes) else value or ''
