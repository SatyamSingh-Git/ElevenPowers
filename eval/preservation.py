"""Explicit staged subscription comparison; never activated by installation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import time
import uuid

from core.config import Config, save
from core.evidence import source_snapshot
from core.hosts.provenance import fingerprint
from core.hosts.readiness import read as diagnostics
from core.hosts.setup import install
from core.ledger import Ledger
from core.milestones import build
from core.parsers import parse
from core.process import run, OutputLimitExceeded
from . import subscription
from .preservation_cases import case
from .preservation_oracles import grade, oracle

TOOL_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_COMMAND = 'python -m unittest discover -s tests -v'
LIMITS = [
    'Two selected authored Python systems; no population effect or large-repository claim.',
    'Guide feedback, milestone advice and receipt handling form one combined intervention.',
    'Native tools have filesystem access; withholding grading paths is not an OS exposure boundary.',
    'Unsigned callback observations are not host authentication.',
    'Stage-final snapshots cannot establish a linked correction after an intervention.',
    'Fresh receipts establish verification, not necessarily improved code.'
]


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes(json.dumps(value, indent=2, allow_nan=False).encode('utf-8'))
    temporary.replace(path)


def _read(path):
    if path.is_symlink() or path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError('linked or oversized controller record')
    return json.loads(path.read_text(encoding='utf-8'))


def _safe(root, name):
    if (not isinstance(name, str) or '\\' in name or ':' in name
            or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts
            or PurePosixPath(name).as_posix() != name):
        raise ValueError('unsafe relative path')
    path = root / name
    for parent in (path, *path.parents):
        if parent.is_symlink() or getattr(parent, 'is_junction', lambda: False)():
            raise ValueError('linked path')
    return path


def _manifest(root):
    values = {}
    size = 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        base = Path(directory)
        dirs[:] = [d for d in dirs if d not in {'.git', '.elevenpowers', '__pycache__', '.pytest_cache'}]
        for name in dirs + files:
            _safe(root, (base / name).relative_to(root).as_posix())
        for name in files:
            path = base / name
            size += path.stat().st_size
            if size > 2 * 1024 * 1024 or len(values) >= 128:
                raise ValueError('candidate file/byte limit')
            relative = path.relative_to(root).as_posix()
            values[relative] = _hash(path.read_bytes())
    return values


def _settings(root):
    names = ['.elevenpowers/config.json', '.claude/settings.local.json', '.claude/settings.json',
             'CLAUDE.md', 'CLAUDE.local.md', 'AGENTS.md', 'AGENTS.override.md',
             'elevenpowers.milestones.json', 'impactgraph.json']
    return {name: _hash(_safe(root, name).read_bytes()) if _safe(root, name).is_file() else None
            for name in names}


def _harness():
    return _hash(b''.join((TOOL_ROOT / name).read_bytes() for name in
        ('eval/preservation.py', 'eval/preservation_cases.py', 'eval/preservation_oracles.py',
         'eval/subscription.py')))


def prepare(destination, *, names=('queue', 'inventory'), seconds=480):
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 1 <= seconds <= 480:
        raise ValueError('invalid total session allowance')
    if not names or len(names) > 2 or len(set(names)) != len(names):
        raise ValueError('one or two distinct frozen cases required')
    cases = [case(name) for name in names]
    root = Path(destination).absolute()
    if root.exists() or root.is_symlink() or any(p.is_symlink() for p in root.parents):
        raise ValueError('new unlinked batch required')
    root.mkdir(parents=True)
    root = root.resolve()
    protocol = {'schema': 1, 'prepared_at': datetime.now(timezone.utc).isoformat(),
                'host': 'claude', 'model': 'claude-sonnet-5', 'effort': 'medium',
                'seconds_per_session': seconds, 'runtime_fingerprint': fingerprint(),
                'harness_sha256': _harness(), 'slots': [], 'seals': {}, 'limits': LIMITS}
    # Alternate which arm goes first; retain order rather than choosing after outcomes.
    for index, value in enumerate(cases):
        arms = ('ordinary', 'assisted') if index % 2 == 0 else ('assisted', 'ordinary')
        for arm in arms:
            slot = value['id'] + '-' + arm
            protocol['slots'].append(slot)
            folder = root / slot
            candidate = folder / 'candidate'
            candidate.mkdir(parents=True)
            for name, text in value['files'].items():
                path = _safe(candidate, name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(text.encode('utf-8'))
            rows = [{'id': 'established-core', 'description': 'Retain existing public core behavior.',
                     'inputs': ['service.py', 'tests/test_core.py'],
                     'checks': [{'kind': 'test_suite', 'command': PUBLIC_COMMAND}]},
                    {'id': 'formatting', 'description': 'Preserve the independent formatting utility.',
                     'inputs': ['formatting.py', 'tests/test_formatting.py'],
                     'checks': [{'kind': 'test_suite', 'command': PUBLIC_COMMAND}]}]
            _write(candidate / 'elevenpowers.milestones.json', {'schema': 1, 'milestones': rows})
            for args in (['init', '-q'], ['add', '.'],
                         ['-c', 'user.name=Preservation control', '-c', 'user.email=control@example.invalid',
                          'commit', '-qm', 'Frozen established behavior']):
                done = run(['git', '-c', f'safe.directory={candidate.as_posix()}', *args],
                           cwd=candidate, timeout=15, shell=False)
                if done.returncode:
                    raise ValueError('disposable Git preparation failed')
            save(candidate, Config(profile='guide' if arm == 'assisted' else 'off',
                auto_detect=False, commands={'tests': PUBLIC_COMMAND}, strength={'enabled': False},
                milestone_advice={'enabled': arm == 'assisted', 'seconds': 1, 'cooldown': 30, 'max_attempts': 3}))
            if arm == 'assisted':
                install('claude', candidate, sys.executable, TOOL_ROOT)
            baseline = grade(value, 0, candidate)
            snapshot = source_snapshot(candidate, fresh=True)
            done = run(PUBLIC_COMMAND, cwd=candidate, timeout=20)
            (folder / 'baseline-output.txt').write_text(done.stdout + done.stderr, encoding='utf-8')
            if baseline['state'] != 'graded' or baseline['failed'] or done.returncode != 0 or not snapshot[0].complete:
                raise ValueError('baseline qualification failed; preserve the batch')
            ledger = Ledger(root=candidate, task='established-behavior')
            ledger.add(parse(PUBLIC_COMMAND, done.stdout + done.stderr, done.returncode, candidate, snapshot=snapshot))
            ledger.save()
            _write(folder / 'baseline.json', baseline)
            protocol['seals'][slot] = {'initial': _manifest(candidate), 'settings': _settings(candidate),
                'baseline': _hash((folder / 'baseline.json').read_bytes()),
                'oracles': [_hash(oracle(value, stage).encode()) for stage in range(3)],
                'session': str(uuid.uuid4()), 'requests': value['requests']}
    _write(root / 'protocol.json', protocol)
    _write(root / 'protocol-seal.json', {'sha256': _hash((root / 'protocol.json').read_bytes())})
    return protocol


def verify(batch, slot, *, initial=False):
    root = Path(batch).resolve(strict=True)
    protocol = _read(root / 'protocol.json')
    allowance = protocol.get('seconds_per_session')
    if (type(allowance) not in (int, float) or not math.isfinite(allowance)
            or not 1 <= allowance <= 480):
        raise ValueError('loaded session allowance exceeds approved bounds')
    if _read(root / 'protocol-seal.json').get('sha256') != _hash((root / 'protocol.json').read_bytes()):
        raise ValueError('sealed protocol changed')
    if slot not in protocol['slots'] or '/' in slot or '\\' in slot:
        raise ValueError('unknown slot')
    seal = protocol['seals'][slot]
    candidate = _safe(root, slot + '/candidate')
    value = case(slot.rsplit('-', 1)[0])
    if protocol['runtime_fingerprint'] != fingerprint() or protocol['harness_sha256'] != _harness():
        raise ValueError('sealed runtime or harness changed')
    if seal['oracles'] != [_hash(oracle(value, stage).encode()) for stage in range(3)]:
        raise ValueError('sealed independent oracle changed')
    if seal['requests'] != value['requests'] or seal['baseline'] != _hash((root / slot / 'baseline.json').read_bytes()):
        raise ValueError('sealed request or baseline changed')
    actual = _manifest(candidate)
    if initial and actual != seal['initial']:
        raise ValueError('sealed initial candidate changed')
    if _settings(candidate) != seal['settings']:
        raise ValueError('sealed project configuration changed')
    for name, expected in seal['initial'].items():
        if initial or name not in value['production']:
            if actual.get(name) != expected:
                raise ValueError('sealed public input changed: ' + name)
    for name in actual.keys() - seal['initial'].keys():
        if not (name.startswith('tests/test_') and name.endswith('.py') and '/' not in name[6:]):
            raise ValueError('candidate added a file outside permitted test scope')
    for name in value['production']:
        if name not in actual:
            raise ValueError('candidate removed production input')
    return protocol, candidate, value


def native_command(executable, root, prompt, session, stage):
    if stage not in (1, 2):
        raise ValueError('invalid request stage')
    args = subscription.command('claude', executable, root, prompt, model='claude-sonnet-5')
    args.remove('--no-session-persistence')
    args[args.index('--output-format') + 1] = 'stream-json'
    args += ['--verbose', '--session-id' if stage == 1 else '--resume', session,
             '--disable-slash-commands', '--disallowedTools', 'WebFetch', 'WebSearch', 'Agent',
             'Bash(curl *)', 'Bash(wget *)', 'Bash(git fetch *)', 'Bash(git clone *)',
             'Bash(pip install *)', 'Bash(npm install *)']
    return args


def _prompt(value, stage):
    return f'''Continue developing this working project. This is stage {stage} of two feature requests.
{value['requests'][stage - 1]}
Edit only service.py and formatting.py; add tests/test_*.py files if useful.
Existing tests, milestone declarations, host configuration and instructions are immutable.
Preserve all earlier behavior and run ordinary verification, including: {PUBLIC_COMMAND}
Use python from PATH. Work only in this candidate directory. Do not inspect parent/sibling
directories, evaluator code or hidden checks. Do not fetch answers, use network tools,
install dependencies, change Git state or delegate to another model. Do not create a
workflow or research plan; implement the feature and its useful tests in this request.
Report the behavior implemented and commands actually run. No hidden grading feedback
will be provided between stages. The same preservation requirements apply to both arms.
'''


def _native(root, protocol, *, since=None, session=None):
    try:
        host = diagnostics(root).get('claude', {})
        phases = host.get('phases', {})
        advice_path = root / '.elevenpowers/advice.json'
        advice = _read(advice_path) if advice_path.exists() else {'tasks': []}
        attempts = [a for t in advice['tasks'] for a in t['attempts']]
        expected_session = _hash(session.encode()) if session else ''
        required = ('SessionStart', 'UserPromptSubmit', 'PostToolUse', 'Stop')
        links = [link for link in host.get('receipt_links', [])
                 if link.get('session') == expected_session and since is not None
                 and link.get('at', 0) >= since
                 and link.get('task') == phases.get('Stop', {}).get('task')]
        edit = phases.get('PostToolUse', {}).get('edit', {})
        qualified = (since is not None and bool(expected_session)
                     and all(phases.get(p, {}).get('processed', 0) > 0
                             and phases[p].get('session') == expected_session
                             and phases[p].get('last_at', 0) >= since for p in required)
                     and phases.get('SessionStart', {}).get('runtime_fingerprint') == protocol['runtime_fingerprint']
                     and edit.get('changed', 0) > 0 and not edit.get('incomplete', True)
                     and edit.get('session') == expected_session and bool(links)
                     and bool(edit.get('task')) and edit.get('task') == phases.get('Stop', {}).get('task')
                     and all(phases.get(p, {}).get('task') == edit.get('task')
                             for p in ('UserPromptSubmit', 'PostToolUse', 'Stop'))
                     and not host.get('errors'))
        return {'state': 'observed' if qualified else 'incomplete', 'phases': phases,
                'receipt_links': len(links),
                'advice_attempts': [{'status': a['status'], 'elapsed_ms': a.get('elapsed_ms')}
                                   for a in attempts]}
    except (OSError, ValueError, KeyError, TypeError):
        return {'state': 'incomplete', 'phases': {}, 'receipt_links': 0, 'advice_attempts': []}


def execute(batch, slot, executable):
    root = Path(batch).resolve(strict=True)
    folder = _safe(root, slot)
    if (folder / 'result.json').exists():
        raise ValueError('attempt already exists; never retry launched slots')
    protocol, candidate, value = verify(root, slot, initial=True)
    if os.environ.get('EP_PROFILE'):
        raise ValueError('profile environment override is not a frozen input')
    record = {'schema': 1, 'slot': slot, 'state': 'preflight', 'stages': [],
              'model_seconds': 0, 'host_version': '', 'limits': LIMITS}
    _write(folder / 'result.json', record)
    version = run([executable, '--version'], cwd=candidate, timeout=10, shell=False)
    record['host_version'] = version.stdout.strip()[:100] if version.returncode == 0 else ''
    if not record['host_version'] or not subscription.auth('claude', executable, candidate):
        record['state'] = 'authentication_or_host_unavailable'
        _write(folder / 'result.json', record)
        return record
    for stage in (1, 2):
        verify(root, slot, initial=stage == 1)
        remaining = protocol['seconds_per_session'] - record['model_seconds']
        allowance = remaining / (3 - stage)
        item = {'stage': stage, 'state': 'running', 'seconds_cap': allowance,
                'source_before': _manifest(candidate), 'launched': True}
        prompt = _prompt(value, stage)
        item['prompt_sha256'] = _hash(prompt.encode())
        (folder / f'prompt-{stage}.txt').write_text(prompt, encoding='utf-8')
        record['stages'].append(item)
        record['state'] = 'running'
        _write(folder / 'result.json', record)
        started = time.monotonic()
        item['started_at'] = time.time()
        output, diagnostic, code = '', '', None
        try:
            done = run(native_command(executable, candidate, prompt, protocol['seals'][slot]['session'], stage),
                       cwd=candidate, timeout=allowance, shell=False)
            output, diagnostic, code = done.stdout, done.stderr, done.returncode
            item['state'] = 'returned' if code == 0 else 'host_failed'
        except (OSError, subprocess.SubprocessError) as error:
            output = getattr(error, 'stdout', '') or ''
            diagnostic = getattr(error, 'stderr', '') or ''
            if isinstance(output, bytes): output = output.decode('utf-8', 'replace')
            if isinstance(diagnostic, bytes): diagnostic = diagnostic.decode('utf-8', 'replace')
            item['state'] = ('timeout' if isinstance(error, subprocess.TimeoutExpired) else
                             'output_limit' if isinstance(error, OutputLimitExceeded) else 'host_unavailable')
        item['elapsed_ms'] = round((time.monotonic() - started) * 1000, 3)
        record['model_seconds'] += item['elapsed_ms'] / 1000
        item['exit_code'] = code
        (folder / f'native-{stage}.jsonl').write_text(output, encoding='utf-8')
        (folder / f'diagnostic-{stage}.txt').write_text(diagnostic, encoding='utf-8')
        result_event = ''
        for line in output.splitlines():
            try:
                event = json.loads(line)
                if isinstance(event, dict) and event.get('type') == 'result': result_event = json.dumps(event)
            except ValueError:
                continue
        item['host_observation'] = subscription.observation('claude', result_event, diagnostic)
        if item['state'] == 'returned':
            item['state'] = 'completed' if item['host_observation']['completed'] else 'host_incomplete'
        try:
            verify(root, slot)
            item['scope'] = 'preserved'
            item['source_after'] = _manifest(candidate)
            source = {name: (candidate / name).read_text(encoding='utf-8') for name in value['production']}
            _write(folder / f'source-{stage}.json', source)
            item['independent_grade'] = grade(value, stage, candidate)
            item['native'] = _native(candidate, protocol, since=item['started_at'],
                                     session=protocol['seals'][slot]['session'])
            item['milestones'] = build(candidate, seconds=10, impact=True)
        except (OSError, ValueError, KeyError, TypeError):
            item['scope'] = 'violated'
            item['state'] = 'scope_violation'
        _write(folder / 'result.json', record)
        if item['state'] != 'completed':
            break
    record['state'] = ('completed' if len(record['stages']) == 2
                       and all(s['state'] == 'completed' and s.get('independent_grade', {}).get('state') == 'graded'
                               for s in record['stages']) else 'incomplete')
    _write(folder / 'result.json', record)
    return record


def summarize(batch):
    root = Path(batch).resolve(strict=True)
    protocol = _read(root / 'protocol.json')
    records = {}
    for slot in protocol['slots']:
        path = root / slot / 'result.json'
        if path.exists(): records[slot] = _read(path)
    complete = len(records) == len(protocol['slots']) and all(r.get('state') == 'completed' for r in records.values())
    rows = []
    for name in dict.fromkeys(slot.rsplit('-', 1)[0] for slot in protocol['slots']):
        row = {'case': name, 'ordinary': None, 'assisted': None, 'difference': None}
        for arm in ('ordinary', 'assisted'):
            record = records.get(name + '-' + arm)
            if record and record.get('state') == 'completed':
                stages = record['stages']
                row[arm] = {'passed': stages[-1]['independent_grade']['passed'],
                            'failed': stages[-1]['independent_grade']['failed'],
                            'model_seconds': round(record['model_seconds'], 3),
                            'stage_passes': [s['independent_grade']['passed'] for s in stages],
                            'native': [s['native']['state'] for s in stages]}
        if row['ordinary'] is not None and row['assisted'] is not None:
            row['difference'] = row['assisted']['passed'] - row['ordinary']['passed']
        rows.append(row)
    return {'schema': 1, 'state': 'complete' if complete else 'incomplete',
            'attempted_slots': len(records), 'expected_slots': len(protocol['slots']), 'pairs': rows,
            'paired_correctness_advantage_observed': complete and any(r['difference'] is not None and r['difference'] > 0 for r in rows),
            'linked_correction_observed': False, 'limits': LIMITS}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare', type=Path)
    action.add_argument('--execute', type=Path)
    action.add_argument('--summary', type=Path)
    parser.add_argument('--slot')
    parser.add_argument('--executable')
    args = parser.parse_args()
    if args.prepare: value = prepare(args.prepare)
    elif args.summary: value = summarize(args.summary)
    else:
        if not args.slot or not args.executable: parser.error('execution requires an explicit slot and installed executable')
        value = execute(args.execute, args.slot, args.executable)
    print(json.dumps(value, indent=2))


if __name__ == '__main__':
    main()
