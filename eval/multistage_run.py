"""Sealed, never-retry multi-stage conversations: superpowers, with and without ElevenPowers.

Borrowed: the seal, never-retry and stream reading of `eval.heldout_run`, and the
resume-per-stage conversation of `eval.preservation`. Added: superpowers is
enabled at project scope in both arms and checked in every turn's init event,
the tree is kept after every stage, and the kept trees are graded by
`eval.multistage_oracles` for lost groups, stale facts and rules. See
docs/superpowers/specs/2026-10-23-multistage-field-claims-design.md.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from core.config import Config, save
from core.hosts.provenance import fingerprint
from core.hosts.setup import install
from core.process import run, OutputLimitExceeded
from . import multistage_oracles as oracles
from . import subscription
from .heldout_run import NETWORK, REACHING_TOOLS, _interpreter, _tool_calls
from .live import CLOSED_BOOK, _sandboxed, _seed_git
from .multistage_cases import load
from .preservation import _read, _write

TOOL_ROOT = Path(__file__).resolve().parents[1]
CASES = TOOL_ROOT / 'eval' / 'multistage_cases'
MANIFEST = TOOL_ROOT / 'results' / 'multistage' / 'manifest.json'
ARMS = ('superpowers', 'elevenpowers')
SUPERPOWERS = 'superpowers@claude-plugins-official'
PROJECT_SETTINGS = {
    'enabledPlugins': {SUPERPOWERS: True},
    'extraKnownMarketplaces': {'claude-plugins-official': {
        'source': {'source': 'github', 'repo': 'anthropics/claude-plugins-official'}}},
}
# The start of ElevenPowers' SessionStart context; superpowers' own says "You have superpowers".
MARK = 'ElevenPowers active'
# Superpowers works through the Skill tool, which the held-out launcher's list leaves out.
TOOLS = 'Bash,Read,Edit,Write,Glob,Grep,Skill'
# A print-mode turn cannot be answered, and a request that stops to ask leaves its stage undone.
UNATTENDED = ("I won't be around to answer questions while you work on this, so make any decisions "
              "yourself and finish the request in this turn.")
KEPT_OUT = ('.git', '.claude', '.elevenpowers', '__pycache__', '.pytest_cache')
HARNESS = ('eval/multistage_run.py', 'eval/multistage_cases.py', 'eval/multistage_oracles.py',
           'eval/subscription.py', 'eval/heldout_run.py', 'eval/heldout_vacuity.py', 'eval/live.py',
           'eval/bundle.py')


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _harness():
    return _hash(b''.join((TOOL_ROOT / name).read_bytes() for name in HARNESS))


def _files(cases, name):
    folder = Path(cases) / name
    return {p.relative_to(folder).as_posix(): _hash(p.read_bytes())
            for p in sorted(folder.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}


def _frozen(frozen, name):
    # The manifest keys each file by its repository path; compare from the case folder down.
    return {key.split(f'/{name}/', 1)[1]: sha
            for key, sha in frozen['cases'].get(name, {}).get('file_sha256', {}).items()}


def prepare(batch, names, *, replicates, seconds=900, model='claude-sonnet-5-5', cases=CASES, manifest=MANIFEST):
    if model not in subscription.SUPPORTED_MODELS['claude']:
        raise ValueError('unsupported subscription model')
    root = Path(batch).absolute()
    if root.exists():
        raise ValueError('new batch required')
    for withheld in (Path(cases).absolute(), Path(manifest).absolute().parent):
        if withheld == root or withheld in root.parents:
            raise ValueError(f'{withheld} is withheld from the agent; the batch cannot live inside it')
    for parent in root.parents:
        for name in ('CLAUDE.md', 'CLAUDE.local.md'):
            if (parent / name).exists():
                raise ValueError(f'{parent / name} is a CLAUDE.md the agent would read; put the batch elsewhere')
    frozen = json.loads(Path(manifest).read_text(encoding='utf-8'))
    for name in names:
        if _files(cases, name) != _frozen(frozen, name):
            raise ValueError(f'{name} differs from the frozen manifest')
        load(Path(cases) / name)
    slots = []
    for replicate in range(replicates):
        for index, name in enumerate(names):
            arms = ARMS if (index + replicate) % 2 == 0 else ARMS[::-1]
            slots += [f'{name}--{arm}--{replicate}' for arm in arms]
    protocol = {'schema': 1, 'prepared_at': datetime.now(timezone.utc).isoformat(), 'host': 'claude',
                'model': model, 'effort': 'medium', 'seconds': seconds, 'replicates': replicates,
                'tools': TOOLS, 'unattended': UNATTENDED, 'cases_root': str(Path(cases).absolute()),
                'manifest': str(Path(manifest).absolute()), 'manifest_commit': frozen.get('commit'),
                'case_sha256': {name: frozen['cases'][name]['sha256'] for name in names},
                'files': {name: _frozen(frozen, name) for name in names},
                'runtime_fingerprint': fingerprint(), 'harness_sha256': _harness(), 'slots': slots,
                'sessions': {slot: str(uuid.uuid4()) for slot in slots}}
    _write(root / 'protocol.json', protocol)
    _write(root / 'protocol-seal.json', {'sha256': _hash((root / 'protocol.json').read_bytes())})
    return protocol


def verify(batch, slot):
    root = Path(batch).resolve(strict=True)
    protocol = _read(root / 'protocol.json')
    if _read(root / 'protocol-seal.json').get('sha256') != _hash((root / 'protocol.json').read_bytes()):
        raise ValueError('sealed protocol changed')
    if slot not in protocol['slots']:
        raise ValueError('unknown slot')
    if protocol['runtime_fingerprint'] != fingerprint() or protocol['harness_sha256'] != _harness():
        raise ValueError('sealed runtime or harness changed')
    name, arm, _ = slot.split('--')
    if _files(protocol['cases_root'], name) != protocol['files'][name]:
        raise ValueError(f'{name} differs from the frozen manifest')
    return protocol, load(Path(protocol['cases_root']) / name), arm


def _workspace(case, folder, arm):
    work = folder / 'work'
    shutil.copytree(Path(case['root']) / 'start', work)
    _write(work / '.claude' / 'settings.json', PROJECT_SETTINGS)
    # Beside the project, not in it, so the interpreter never enters the agent's tree or its diffs.
    _interpreter(sys.executable, folder)
    if arm == 'elevenpowers':
        save(work, Config(profile='guide', commands={'tests': f"python -m pytest {case['test_dir']} -q"}))
        install('claude', work, sys.executable, TOOL_ROOT)
    _seed_git(work)
    shutil.copytree(work, folder / 'snapshots' / '0', ignore=shutil.ignore_patterns(*KEPT_OUT))
    return work


def command(executable, work, prompt, session, stage, model):
    args = subscription.command('claude', executable, work, prompt, model=model)
    args.remove('--no-session-persistence')
    args[args.index('--output-format') + 1] = 'stream-json'
    args[args.index('--tools') + 1] = TOOLS
    args.insert(args.index('--allowedTools') + 1, 'Skill')
    return args + ['--verbose', '--session-id' if stage == 1 else '--resume', session,
                   '--disallowedTools', *CLOSED_BOOK]


def _events(output):
    events = []
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _breaches(calls, cases_root, manifest):
    hidden = (Path(cases_root).as_posix().lower(), Path(manifest).parent.as_posix().lower(),
              'elevenpowers-multistage-cases')
    found = []
    for call in calls:
        raw = '\n'.join(str(value) for value in call.get('input', {}).values())
        text = raw.replace('\\', '/').lower()
        command = str(call.get('input', {}).get('command', ''))
        if (call.get('name') in REACHING_TOOLS or (call.get('name') == 'Bash' and NETWORK.search(command))
                or any(path in text for path in hidden)):
            found.append(f"{call.get('name')}: {raw[:200]}")
    return found


def grade(case, snapshots):
    """Graded from the kept trees alone, so a batch can be regraded without its workspaces."""
    trees = [Path(snapshots) / str(n) for n in sorted(int(p.name) for p in Path(snapshots).iterdir())]
    previous = base = oracles.groups(case, 0, trees[0])
    stages = []
    for n in range(1, len(trees)):
        current = oracles.groups(case, n, trees[n])
        stages.append({'stage': n, 'groups': current, 'lost': oracles.regressions(case, n, previous, current),
                       'stale': oracles.stale(case, n, trees[n]),
                       'new': sorted(g['id'] for g in case['groups']
                                     if g['since'] == n and current.get(g['id']) == 'passed'),
                       **oracles.rules(case, n, trees[n - 1], trees[n])})
        previous = current
    return {'base': base, 'stages': stages, 'lost': sum(len(s['lost']) for s in stages),
            'stale': sum(len(s['stale']) for s in stages)}


def execute(batch, slot, executable):
    root = Path(batch).resolve(strict=True)
    folder = root / slot
    if (folder / 'result.json').exists():
        raise ValueError('attempt already exists; never retry launched slots')
    protocol, case, arm = verify(root, slot)
    session = protocol['sessions'][slot]
    record = {'schema': 1, 'slot': slot, 'case': case['id'], 'arm': arm, 'state': 'preflight', 'stages': [],
              'cost': 0.0, 'seconds': 0.0}
    _write(folder / 'result.json', record)
    version = run([executable, '--version'], cwd=folder, timeout=10, shell=False)
    record['host_version'] = version.stdout.strip()[:100] if version.returncode == 0 else ''
    if not record['host_version'] or not subscription.auth('claude', executable, folder):
        record['state'] = 'authentication_or_host_unavailable'
        _write(folder / 'result.json', record)
        return record

    work = _workspace(case, folder, arm)
    # Claude Code otherwise sends small auxiliary calls to Haiku, which the exact-model rule refuses.
    environment = {**_sandboxed(folder), 'ANTHROPIC_DEFAULT_HAIKU_MODEL': protocol['model']}
    spent = 0.0
    for stage in range(1, len(case['stages']) + 1):
        verify(root, slot)
        prompt = case['stages'][stage - 1]['request'] + '\n\n' + UNATTENDED
        item = {'stage': stage, 'state': 'running', 'prompt_sha256': _hash(prompt.encode())}
        record['stages'].append(item)
        record['state'] = 'running'
        _write(folder / 'result.json', record)
        started = time.monotonic()
        try:
            done = run(command(executable, work, prompt, session, stage, protocol['model']), cwd=work,
                       timeout=protocol['seconds'], shell=False, env=environment)
            output, diagnostic = done.stdout, done.stderr
            state = 'returned' if done.returncode == 0 else 'host_failed'
        except (OSError, subprocess.SubprocessError) as error:
            output, diagnostic = getattr(error, 'stdout', '') or '', getattr(error, 'stderr', '') or ''
            if isinstance(output, bytes): output = output.decode('utf-8', 'replace')
            if isinstance(diagnostic, bytes): diagnostic = diagnostic.decode('utf-8', 'replace')
            state = ('timeout' if isinstance(error, subprocess.TimeoutExpired) else
                     'output_limit' if isinstance(error, OutputLimitExceeded) else 'host_unavailable')
        item['seconds'] = round(time.monotonic() - started, 3)
        (folder / f'native-{stage}.jsonl').write_text(output, encoding='utf-8')
        (folder / f'diagnostic-{stage}.txt').write_text(diagnostic, encoding='utf-8')

        events = _events(output)
        calls, result = _tool_calls(output)
        item['observation'] = subscription.observation('claude', json.dumps(result) if result else '', diagnostic)
        # A resumed session reports its cost so far; this turn's is the difference.
        total = float(result.get('total_cost_usd') or 0)
        item['cost'] = round(total - spent, 6) if result else 0.0
        spent = total if result else spent
        inits = [e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init']
        item['superpowers'] = bool(inits) and all(
            SUPERPOWERS in [p.get('source') for p in e.get('plugins', [])] for e in inits)
        item['elevenpowers'] = any(e.get('subtype') == 'hook_response' and MARK in str(e.get('output', ''))
                                   for e in events)
        item['breaches'] = _breaches(calls, protocol['cases_root'], protocol.get('manifest', MANIFEST))
        if state == 'returned':
            state = 'completed' if item['observation']['completed'] else 'host_incomplete'
            if item['observation']['models'] != [protocol['model']]:
                state = 'model_unqualified'
            elif result.get('session_id') != session:
                state = 'conversation_unqualified'
            elif not item['superpowers'] or item['elevenpowers'] != (arm == 'elevenpowers'):
                state = 'plugins_unqualified'
            elif item['breaches']:
                state = 'closed_book_breach'
        item['state'] = state
        shutil.copytree(work, folder / 'snapshots' / str(stage), ignore=shutil.ignore_patterns(*KEPT_OUT))
        record['seconds'] = round(record['seconds'] + item['seconds'], 3)
        record['cost'] = round(spent, 6)
        _write(folder / 'result.json', record)
        if state != 'completed':
            break
    record['state'] = ('completed' if len(record['stages']) == len(case['stages'])
                       and all(s['state'] == 'completed' for s in record['stages']) else 'incomplete')
    record['grade'] = grade(case, folder / 'snapshots')
    _write(folder / 'result.json', record)
    return record


def collect(batch, *, regrade=False):
    """One row per scheduled slot; a slot never launched is counted, not dropped."""
    root = Path(batch).resolve(strict=True)
    protocol = _read(root / 'protocol.json')
    rows = []
    for slot in protocol['slots']:
        name, arm, replicate = slot.split('--')
        row = {'slot': slot, 'case': name, 'arm': arm, 'replicate': int(replicate), 'state': 'not_launched',
               'comparable': False, 'lost': None, 'stale': None}
        path = root / slot / 'result.json'
        if path.exists():
            record = _read(path)
            case = load(Path(protocol['cases_root']) / name)
            graded = (grade(case, root / slot / 'snapshots')
                      if regrade and (root / slot / 'snapshots').is_dir() else record.get('grade'))
            row.update(state=record['state'], stages=len(record['stages']), cost=record['cost'],
                       seconds=record['seconds'], grade=graded,
                       comparable=record['state'] == 'completed' and bool(graded)
                       and len(graded['stages']) == len(case['stages']),
                       lost=graded['lost'] if graded else None, stale=graded['stale'] if graded else None)
        rows.append(row)
    return rows


def headroom(rows):
    """The pilot's go: something went wrong in a complete superpowers-only conversation."""
    return any(row['arm'] == 'superpowers' and row['comparable'] and (row['lost'] or row['stale']) for row in rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    prepared = commands.add_parser('prepare')
    prepared.add_argument('--batch', type=Path, required=True, help='outside any folder holding a CLAUDE.md')
    chosen = prepared.add_mutually_exclusive_group(required=True)
    chosen.add_argument('--cases', nargs='+')
    chosen.add_argument('--pilot', action='store_true', help="the manifest's pilot cases")
    prepared.add_argument('--cases-root', type=Path, default=CASES)
    prepared.add_argument('--manifest', type=Path, default=MANIFEST)
    prepared.add_argument('--replicates', type=int, default=1)
    prepared.add_argument('--seconds', type=int, default=900)
    executed = commands.add_parser('execute')
    executed.add_argument('--batch', type=Path, required=True)
    executed.add_argument('--slot', required=True)
    executed.add_argument('--executable', default='claude')
    collected = commands.add_parser('collect')
    collected.add_argument('--batch', type=Path, required=True)
    collected.add_argument('--out', type=Path, required=True)
    collected.add_argument('--regrade', action='store_true', help='grade again from the kept snapshots')
    args = parser.parse_args(argv)
    if args.action == 'prepare':
        names = json.loads(args.manifest.read_text(encoding='utf-8'))['pilot']['cases'] if args.pilot else args.cases
        value = prepare(args.batch, names, replicates=args.replicates, seconds=args.seconds,
                        cases=args.cases_root, manifest=args.manifest)
        print(len(value['slots']), 'slots sealed:', ' '.join(value['slots']))
    elif args.action == 'execute':
        record = execute(args.batch, args.slot, args.executable)
        print(json.dumps({k: record.get(k) for k in ('slot', 'state', 'cost', 'seconds')}),
              json.dumps({k: record.get('grade', {}).get(k) for k in ('lost', 'stale')}))
    else:
        rows = collect(args.batch, regrade=args.regrade)
        args.out.write_text(json.dumps(rows, indent=2) + '\n', encoding='utf-8')
        print(len(rows), 'scheduled;', sum(r['comparable'] for r in rows), 'comparable; headroom', headroom(rows))


if __name__ == '__main__':
    main()
