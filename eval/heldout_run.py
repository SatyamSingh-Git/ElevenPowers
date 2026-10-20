"""Sealed, never-retry subscription runs of held-out tasks, ordinary against assisted.

Borrowed: the seal and never-retry discipline of `eval.preservation`; the
workspace, closed-book tool list, patch export and grading of `eval.live`;
VACUOUS from `eval.heldout_vacuity`. Added: each task runs on its own
closed-book interpreter, and every tool call that reaches outside the workspace
is recorded with the run instead of being trusted to the denial list.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

from core.config import Config, save
from core.hosts.provenance import fingerprint
from core.hosts.setup import install
from core.process import run, OutputLimitExceeded
from . import subscription
from .bundle import export_patch
from .heldout_env import _python, canary
from .heldout_vacuity import vacuity
from .live import CLOSED_BOOK, _sandboxed, _seed_git, base_tree, grade_patch, materialise
from .preservation import _read, _write
from .task import Task

TOOL_ROOT = Path(__file__).resolve().parents[1]
ARMS = ('ordinary', 'assisted')
NAME = re.compile(r'[A-Za-z0-9._-]{1,120}')
NETWORK = re.compile(r'\b(?:curl|wget|Invoke-WebRequest|iwr|gh|pip3?\s+(?:install|download)'
                     r'|git\s+(?:clone|fetch|pull|ls-remote))\b')
# The workspace history is one seed commit, so reading it reveals nothing; recorded, not disqualifying.
HISTORY = re.compile(r'\bgit\s+(?:log|show|blame|reflog)\b')
REACHING_TOOLS = {'WebFetch', 'WebSearch', 'Agent', 'Task'}
HARNESS = ('eval/heldout_run.py', 'eval/live.py', 'eval/heldout_vacuity.py', 'eval/heldout_env.py',
           'eval/bundle.py', 'eval/subscription.py')


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _harness():
    return _hash(b''.join((TOOL_ROOT / name).read_bytes() for name in HARNESS))


def prepare(batch, corpus, *, replicates=3, seconds=900, model='claude-sonnet-5-5'):
    if model not in subscription.SUPPORTED_MODELS['claude']:
        raise ValueError('unsupported subscription model')
    root = Path(batch).absolute()
    if root.exists():
        raise ValueError('new batch required')
    data = Path(corpus).read_bytes()
    names = [task['name'] for task in json.loads(data)['tasks']]
    if len(set(names)) != len(names) or not all(NAME.fullmatch(n) and '--' not in n for n in names):
        raise ValueError('task names must be distinct and path-safe')
    root.mkdir(parents=True)
    (root / 'corpus.json').write_bytes(data)
    slots = []
    for replicate in range(replicates):
        for index, name in enumerate(names):
            arms = ARMS if (index + replicate) % 2 == 0 else ARMS[::-1]
            slots += [f'{name}--{arm}--{replicate}' for arm in arms]
    protocol = {'schema': 1, 'prepared_at': datetime.now(timezone.utc).isoformat(), 'host': 'claude',
                'model': model, 'effort': 'medium', 'seconds': seconds, 'replicates': replicates,
                'runtime_fingerprint': fingerprint(), 'harness_sha256': _harness(),
                'corpus_sha256': _hash(data), 'slots': slots}
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
    data = (root / 'corpus.json').read_bytes()
    if _hash(data) != protocol['corpus_sha256']:
        raise ValueError('sealed corpus changed')
    if protocol['runtime_fingerprint'] != fingerprint() or protocol['harness_sha256'] != _harness():
        raise ValueError('sealed runtime or harness changed')
    name, arm, _ = slot.split('--')
    return protocol, load_task(json.loads(data), name), arm


def load_task(corpus, name):
    entry = next(task for task in corpus['tasks'] if task['name'] == name)
    source = {**entry, 'test_dir': corpus['environments'][entry['url']]['test_dir'].rstrip('/')}
    return Task(name=name, prompt=entry['prompt'], files={}, hidden='', why='', source=source)


def _interpreter(python, work):
    """A workspace venv that sees the task's closed-book packages and nothing else.

    Not `--system-site-packages`: a venv made from a venv inherits the base
    interpreter's site, where the task's own package is usually installed.
    """
    home = work / '.venv'
    run([python, '-m', 'venv', '--without-pip', str(home)], cwd=work, timeout=180, shell=False)
    where = '-c', 'import sysconfig; print(sysconfig.get_paths()["purelib"])'
    shared = run([python, *where], cwd=work, timeout=60, shell=False).stdout.strip()
    own = run([_python(home), *where], cwd=work, timeout=60, shell=False).stdout.strip()
    (Path(own) / 'heldout-task.pth').write_text(shared + '\n', encoding='utf-8')
    return home


def _tool_calls(output):
    calls, result = [], {}
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get('type') == 'result':
            result = event
        elif event.get('type') == 'assistant':
            calls += [item for item in event.get('message', {}).get('content', [])
                      if isinstance(item, dict) and item.get('type') == 'tool_use']
    return calls, result


def execute(batch, slot, executable):
    root = Path(batch).resolve(strict=True)
    folder = root / slot
    if (folder / 'result.json').exists():
        raise ValueError('attempt already exists; never retry launched slots')
    protocol, task, arm = verify(root, slot)
    record = {'schema': 1, 'slot': slot, 'task': task.name, 'arm': arm, 'state': 'preflight',
              'resolved': None, 'vacuous': None, 'seconds': 0, 'cost': 0.0,
              'prompt_sha256': _hash(task.prompt.encode())}
    _write(folder / 'result.json', record)
    version = run([executable, '--version'], cwd=folder, timeout=10, shell=False)
    record['host_version'] = version.stdout.strip()[:100] if version.returncode == 0 else ''
    if not record['host_version'] or not subscription.auth('claude', executable, folder):
        record['state'] = 'authentication_or_host_unavailable'
        _write(folder / 'result.json', record)
        return record

    work = folder / 'work'
    materialise(task, work)
    home = _interpreter(task.source['python'], work)
    if arm == 'assisted':
        save(work, Config(profile='guide', commands={'tests': f"python -m pytest {task.source['test_dir']} -q"}))
        install('claude', work, sys.executable, TOOL_ROOT)
    _seed_git(work)
    # Outside the workspace, so the answer could only come from the interpreter's own site.
    if not canary(_python(home), task.source['import_names'], folder):
        record['state'] = 'canary_failed'
        _write(folder / 'result.json', record)
        return record

    command = subscription.command('claude', executable, work, task.prompt, model=protocol['model'])
    command[command.index('--output-format') + 1] = 'stream-json'
    command += ['--verbose', '--disallowedTools', *CLOSED_BOOK]
    # Claude Code otherwise sends small auxiliary calls to Haiku, which the exact-model rule refuses.
    environment = {**_sandboxed(work), 'ANTHROPIC_DEFAULT_HAIKU_MODEL': protocol['model']}
    record['state'] = 'running'
    _write(folder / 'result.json', record)
    started = time.monotonic()
    try:
        done = run(command, cwd=work, timeout=protocol['seconds'], shell=False, env=environment)
        output, diagnostic = done.stdout, done.stderr
        state = 'returned' if done.returncode == 0 else 'host_failed'
    except (OSError, subprocess.SubprocessError) as error:
        output, diagnostic = getattr(error, 'stdout', '') or '', getattr(error, 'stderr', '') or ''
        if isinstance(output, bytes): output = output.decode('utf-8', 'replace')
        if isinstance(diagnostic, bytes): diagnostic = diagnostic.decode('utf-8', 'replace')
        state = ('timeout' if isinstance(error, subprocess.TimeoutExpired) else
                 'output_limit' if isinstance(error, OutputLimitExceeded) else 'host_unavailable')
    record['seconds'] = round(time.monotonic() - started, 3)
    (folder / 'native.jsonl').write_text(output, encoding='utf-8')
    (folder / 'diagnostic.txt').write_text(diagnostic, encoding='utf-8')

    calls, result = _tool_calls(output)
    record['observation'] = subscription.observation('claude', json.dumps(result) if result else '', diagnostic)
    record['cost'] = float(result.get('total_cost_usd') or 0)
    commands = [str(call.get('input', {}).get('command', '')) for call in calls if call.get('name') == 'Bash']
    record['breaches'] = ([c for c in commands if NETWORK.search(c)]
                          + [call['name'] for call in calls if call.get('name') in REACHING_TOOLS])
    record['history_reads'] = [c for c in commands if HISTORY.search(c)]

    patch = export_patch(work)
    (folder / 'patch.diff').write_bytes(patch.encode('utf-8'))
    graded = grade_patch(task, patch, folder / 'court')
    record.update(resolved=graded.resolved, outcome=graded.outcome, detail=graded.detail)
    if graded.resolved:
        base_tree(task, folder / 'base')
        value = vacuity(folder / 'base', patch, python=task.source['python'], env=task.source.get('env') or {},
                        test_dir=task.source['test_dir'], work=folder / 'vacuity')
        record.update(vacuous=value['vacuous'], vacuity_reason=value['reason'])
    if state == 'returned':
        state = 'graded' if record['observation']['completed'] else 'host_incomplete'
        if record['observation']['models'] != [protocol['model']]:
            state = 'model_unqualified'
        elif state == 'graded' and record['breaches']:
            state = 'closed_book_breach'
    record['state'] = state
    _write(folder / 'result.json', record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    prepared = commands.add_parser('prepare')
    prepared.add_argument('--batch', type=Path, required=True, help='outside any Git ancestor')
    prepared.add_argument('--corpus', type=Path, required=True)
    prepared.add_argument('--replicates', type=int, default=3)
    prepared.add_argument('--seconds', type=int, default=900)
    executed = commands.add_parser('execute')
    executed.add_argument('--batch', type=Path, required=True)
    executed.add_argument('--slot', required=True)
    executed.add_argument('--executable', default='claude')
    args = parser.parse_args()
    if args.action == 'prepare':
        value = prepare(args.batch, args.corpus, replicates=args.replicates, seconds=args.seconds)
        print(len(value['slots']), 'slots sealed')
    else:
        print(json.dumps(execute(args.batch, args.slot, args.executable), indent=2))


if __name__ == '__main__':
    main()
