"""Explicit bounded execution of project-declared checks for an exact patch."""
from pathlib import Path
import subprocess
import time
import uuid

from ..config import load
from ..evidence import Result
from ..hosts.readiness import receipt_key
from ..jobs import Session, Busy
from ..ledger import Ledger
from ..parsers import parse, DECLARED_KINDS
from .. import process
from .execution_state import digest, read, retain, save, witness, _source_witness
from .planning import plan
from .report import build
from ..export import _text as literal
from ..redact import scrub_values
from ..inputs.execution import from_witness
from ..inputs.receipts import attach


def verify(root, base='HEAD~1', head='HEAD', *, seconds=120, command_seconds=30, impact=False, reuse=True):
    """Execute only after exact clean preflight; preserve every unfinished attempt."""
    started = time.monotonic()
    root = Path(root).resolve(strict=True)
    planned = plan(root, base, head, seconds=seconds, command_seconds=command_seconds, impact=impact, reuse=reuse)
    deadline = started + seconds
    result = {'schema_version': 1, 'kind': 'patchproof_verification', 'state': 'incomplete',
              'patch_id': planned['patch_id'], 'checks': [], 'issues': list(planned['issues']),
              'budgets': planned['budgets'], 'bundle': planned['bundle']}
    result['planned_patch'] = {name: planned['bundle']['patch'][name]
                               for name in ('base', 'head', 'patch_id', 'content_digest')}
    for check in planned['checks']:
        result['checks'].append({'properties': check['properties'], 'command': check['command'],
                                 'status': 'deferred', 'receipt_keys': []})
    if not planned['ready'] or time.monotonic() >= deadline:
        return result
    patch = planned['bundle']['patch']
    try:
        # Do not replace damaged state and silently discard a later failed attempt.
        saved = read(root)
        expected, _ = _source_witness(root, patch, deadline, base=base, head=head)
        ledger = Ledger.load(root)
        with Session(root, ledger.task, seconds=max(0, deadline - time.monotonic())) as session:
            saved = read(root)  # A former owner may have written before we obtained the lock.
            for check, outcome in zip(planned['checks'], result['checks']):
                config = load(root)
                command = config.commands.get(check['properties'][0], '')
                try:
                    before, snapshot = witness(root, patch, deadline, base=base, head=head,command=command)
                    if _source_fields(before) != expected:
                        raise ValueError('verification inputs changed since preflight')
                    session.budget.timeout(command_seconds)
                except (OSError, ValueError, TimeoutError, subprocess.SubprocessError) as error:
                    result['issues'].append(type(error).__name__ + ': execution preflight unavailable')
                    break
                if (digest(command) != check['command_digest'] or not config.verifies
                        or any(config.commands.get(p) != command for p in check['properties'])):
                    result['issues'].append('declared commands changed since planning')
                    break
                # Reinspect latest receipt/state under ownership before reuse.
                if check['action'] == 'reuse':
                    fresh = plan(root, base, head,
                                 seconds=max(0, deadline - time.monotonic()), command_seconds=command_seconds)
                    reusable = next((c for c in fresh['checks'] if c['command_digest'] == check['command_digest']), None)
                    final_reuse, _ = witness(root, patch, deadline, base=base, head=head,command=command)
                    if not fresh['ready'] or fresh['patch_id'] != planned['patch_id'] or final_reuse != before:
                        result['issues'].append('requested patch or execution inputs moved during reuse inspection')
                        break
                    if fresh['ready'] and reusable and reusable['action'] == 'reuse':
                        outcome.update(status='reused', receipt_keys=reusable['receipt_keys'])
                        continue
                job = session.queue('patch verification', command)
                item = {'id': uuid.uuid4().hex, 'run': session.data['id'],
                        'properties': check['properties'], 'command_digest': digest(command),
                        'witness': before, 'receipt_keys': [], 'status': 'incomplete',
                        'budgets': planned['budgets'], 'started': time.time()}
                retain(saved, item)
                save(root, saved)
                provisional = parse(command, 'explicit patch verification started', None, root, snapshot=snapshot)
                if 'external_inputs_fingerprint' in before:
                    attach(provisional,from_witness(before),from_witness(None),digest(item['id']))
                ledger.add(provisional); ledger.save()
                item['receipt_keys'] = _aggregates(provisional, check['properties'])
                save(root, saved)
                session.begin(job)
                code, output, interruption = None, '', None
                try:
                    done = process.run(command, cwd=root, shell=True,
                                       timeout=min(command_seconds, max(0, deadline - time.monotonic())))
                    code = done.returncode
                    output = (done.stdout or '') + (done.stderr or '')
                except BaseException as error:
                    # Never export exception bodies or output. The existing local
                    # ledger may retain bounded redacted parser details as before.
                    output = _text(getattr(error, 'stdout', '')) + _text(getattr(error, 'stderr', ''))
                    if not isinstance(error, (OSError, subprocess.SubprocessError)):
                        interruption = error
                after = None
                try:
                    after, _ = witness(root, patch, deadline, base=base, head=head,command=command)
                    if after != before:
                        raise ValueError('execution inputs changed during the command')
                except (OSError, ValueError, TimeoutError, subprocess.SubprocessError):
                    snapshot[0].issues.append('execution inputs changed or final inspection was incomplete')
                records = parse(command, output, code, root, snapshot=snapshot)
                attach(records,from_witness(before),from_witness(after),digest(item['id']))
                ledger.add(records); ledger.save()
                status = ('incomplete' if code is None else 'stale' if snapshot[0].issues else
                          'incomplete' if not records or any(not e.ran_tests for e in records) else
                          'failed' if code or any(e.result is not Result.PASS for e in records)
                          else 'passed')
                item.update(status=status, after=after, exit_code=code, finished=time.time(),
                            receipt_keys=_aggregates(records, check['properties']))
                save(root, saved)
                session.finish(job, status, exit_code=code)
                outcome.update(status=status, receipt_keys=item['receipt_keys'])
                if interruption:
                    raise interruption
                if snapshot[0].issues:
                    result['issues'].append('execution input qualification changed; later commands were deferred')
                    break
    except (OSError, ValueError, Busy, TimeoutError, subprocess.SubprocessError) as error:
        result['issues'].append(type(error).__name__ + ': explicit verification unavailable or incomplete')
    result['bundle'] = build(root, base, head, timeout=max(0, deadline - time.monotonic()), impact=impact)
    states = {check['status'] for check in result['checks']}
    observations = result['bundle']['execution']['checks']
    qualified = all(any(set(e['properties']) == set(c['properties']) and e['association'] == 'bound'
                    and e['status'] == ('passed' if c['status'] == 'reused' else c['status'])
                    for e in observations) for c in result['checks'])
    if not result['issues'] and result['bundle']['binding']['state'] == 'bound' and qualified:
        if states and states <= {'passed', 'reused'}:
            result['state'] = 'passed'
        elif 'failed' in states and not states.intersection({'deferred', 'incomplete', 'stale'}):
            result['state'] = 'failed'
    elif not qualified:
        result['issues'].append('final saved execution associations are unavailable; command results remain visible')
    result['elapsed_seconds'] = round(time.monotonic() - started, 3)
    return result


def _text(value):
    return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else value or ''


def _source_fields(value):
    return {k:v for k,v in value.items() if not k.startswith('external_inputs_')}


def _aggregates(records, properties):
    # Ledger persistence redacts the entire payload, including receipt identity.
    # Associate the saved form, not an in-memory pre-redaction identity.
    return [receipt_key(scrub_values(e.to_dict())) for e in records if e.declaration in properties
            and e.kind is DECLARED_KINDS[e.declaration]]


def markdown(value):
    from .report import markdown as bundle_markdown
    lines = ['# ElevenPowers explicit patch verification', '',
             'Declared verification result: ' + literal(value['state']),
             'This is a qualified command outcome, not universal patch safety.', '',
             '| Properties | Execution | Declared command |', '|---|---|---|']
    for check in value['checks']:
        lines.append('| ' + ' | '.join(literal(v) for v in (
            ', '.join(check['properties']), check['status'], check['command'])) + ' |')
    lines += ['', *['- ' + literal(i) for i in value['issues']], '', bundle_markdown(value['bundle'])]
    return '\n'.join(lines) + '\n'
