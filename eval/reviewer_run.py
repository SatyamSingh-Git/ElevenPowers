"""Sealed, never-retry reviewer calls for the reviewer study (PLAN 13 A.3).

Borrowed: eval.multistage_run's seal and never-retry, and eval.subscription's
launcher flags, which keep the user's own CLAUDE.md out. Added: everything a
reviewer reads (the diff, and in arm `report` ep_review's report) is computed
once at prepare and frozen under the seal, the $0 gate judges exactly those
frozen reports, and the prompt goes in on stdin with no tools, because the
median prompt is longer than a Windows command line allows.
See docs/superpowers/specs/2026-11-01-reviewer-benefit-design.md.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time

from core.export import _portable
from core.review import markdown, review
from . import subscription
from .preservation import _read, _write
from .reviewer_seeds import judge, tally
from .reviewer_study import ARMS, analyse, answer, grade, prompt

TOOL_ROOT = Path(__file__).resolve().parents[1]
HARNESS = ('eval/reviewer_run.py', 'eval/reviewer_study.py', 'eval/reviewer_seeds.py', 'eval/subscription.py',
           'core/review.py')
TIMEOUT = 600
ORDER = 20261101  # seed order is shuffled once, with this fixed seed, so a case's seeds are not run back to back


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _harness():
    return _hash(b''.join((TOOL_ROOT / name).read_bytes() for name in HARNESS))


def command(program, model):
    """The subscription launcher's flags, with the prompt left for stdin and no tools at all."""
    args = subscription.command('claude', 'PROGRAM', Path('.'), 'PROMPT', model=model)
    args.remove('PROMPT')
    args[args.index('--tools') + 1] = ''
    del args[args.index('--allowedTools'):]
    at = args.index('PROGRAM')
    return [*args[:at], *program, *args[at + 1:]]


def _frozen(job):
    repo, base, tests, limits = job
    return _portable(review(Path(repo), base, command=tests, strength=True, limits=limits), Path(repo))


def prepare(batch, seeds, manifest, *, model='claude-sonnet-5-5', limits=None, workers=4):
    root = Path(batch).absolute()
    if root.exists():
        raise ValueError('new batch required')
    for parent in root.parents:
        if (parent / 'CLAUDE.md').exists():
            raise ValueError(f'{parent / "CLAUDE.md"} is a CLAUDE.md a reviewer would read; put the batch elsewhere')
    if model not in subscription.SUPPORTED_MODELS['claude']:
        raise ValueError('unsupported subscription model')
    inputs = root / 'inputs'
    inputs.mkdir(parents=True)
    frozen, rows = {}, []
    # Each report runs its own suites and mutations; separate processes keep them apart.
    jobs = [(str(Path(seeds) / seed['seed']), seed['base'], seed['command'].replace('"python"', f'"{sys.executable}"', 1),
             limits) for seed in manifest['seeds']]
    with ProcessPoolExecutor(workers) as pool:
        reports = list(pool.map(_frozen, jobs))
    for seed, report in zip(manifest['seeds'], reports):
        repo = Path(seeds) / seed['seed']
        diff = subprocess.run(['git', '-c', 'core.autocrlf=false', 'diff', '--no-color', '--no-ext-diff', seed['base'],
                               'HEAD'], cwd=repo, capture_output=True, check=True).stdout.decode('utf-8', 'replace')
        rows.append(judge(seed, report))
        text = markdown(report)
        (inputs / f"{seed['seed']}.diff").write_text(diff, encoding='utf-8', newline='')
        (inputs / f"{seed['seed']}.md").write_text(text, encoding='utf-8', newline='')
        _write(inputs / f"{seed['seed']}.json", report)
        frozen[seed['seed']] = {**seed, 'diff_sha256': _hash(diff.encode('utf-8')),
                                'report_sha256': _hash(text.encode('utf-8'))}
    names = sorted(frozen)
    random.Random(ORDER).shuffle(names)
    slots = [f'{name}--{arm}' for index, name in enumerate(names)
             for arm in (ARMS if index % 2 == 0 else ARMS[::-1])]
    # Preparing calls no model, so it runs where the CLI is absent (hosted CI); `run` checks sign-in.
    program = shutil.which('claude')
    version = subprocess.run([program, '--version'], capture_output=True, text=True).stdout.strip() if program else ''
    protocol = {'schema': 1, 'prepared_at': datetime.now(timezone.utc).isoformat(), 'host': 'claude', 'model': model,
                'effort': 'medium', 'cli': version, 'limits': limits or {}, 'seeds': frozen,
                'slots': slots, 'harness_sha256': _harness(), 'gate': tally(rows)}
    _write(root / 'protocol.json', protocol)
    _write(root / 'protocol-seal.json', {'sha256': _hash((root / 'protocol.json').read_bytes())})
    _write(root / 'gate.json', {'tally': tally(rows), 'rows': rows})
    return protocol, {'tally': tally(rows), 'rows': rows}


def verify(root, slot):
    protocol = _read(root / 'protocol.json')
    if _read(root / 'protocol-seal.json').get('sha256') != _hash((root / 'protocol.json').read_bytes()):
        raise ValueError('sealed protocol changed')
    if protocol['harness_sha256'] != _harness():
        raise ValueError('sealed harness changed')
    if slot not in protocol['slots']:
        raise ValueError('unknown slot')
    name = slot.rsplit('--', 1)[0]
    seed = protocol['seeds'][name]
    if (_hash((root / 'inputs' / f'{name}.diff').read_bytes()) != seed['diff_sha256']
            or _hash((root / 'inputs' / f'{name}.md').read_bytes()) != seed['report_sha256']):
        raise ValueError(f'a frozen input of {name} changed')
    return protocol, seed


def execute(batch, slot, program):
    root = Path(batch).resolve(strict=True)
    protocol, seed = verify(root, slot)
    folder = root / 'slots' / slot
    if folder.exists():
        raise ValueError('attempt already exists; never retry launched slots')
    folder.mkdir(parents=True)
    _write(folder / 'launched.json', {'at': datetime.now(timezone.utc).isoformat()})
    arm = slot.rsplit('--', 1)[1]
    name = seed['seed']
    report = (root / 'inputs' / f'{name}.md').read_text(encoding='utf-8') if arm == 'report' else None
    text = prompt(seed['request'], (root / 'inputs' / f'{name}.diff').read_text(encoding='utf-8'), report)
    started, timed_out, code = time.monotonic(), False, None
    try:
        done = subprocess.run(command(program, protocol['model']), cwd=folder, input=text, capture_output=True,
                              text=True, encoding='utf-8', errors='replace', timeout=TIMEOUT)
        output, code = done.stdout, done.returncode
        (folder / 'diagnostic.txt').write_text(done.stderr[-20000:], encoding='utf-8')
    except subprocess.TimeoutExpired as error:
        timed_out, output = True, error.stdout.decode('utf-8', 'replace') if isinstance(error.stdout, bytes) else ''
    (folder / 'output.json').write_text(output, encoding='utf-8')
    try:
        value = json.loads(output)
    except ValueError:
        value = {}
    reply = answer(value['result']) if isinstance(value.get('result'), str) else None
    result = {'slot': slot, 'seed': name, 'kind': seed['kind'], 'arm': arm,
              'state': 'graded' if reply else 'timed_out' if timed_out else 'unreadable' if value else 'failed',
              'caught': grade(seed, reply), 'decision': reply and reply['decision'],
              'cost': value.get('total_cost_usd'), 'seconds': round(time.monotonic() - started, 1),
              'output_tokens': (value.get('usage') or {}).get('output_tokens'),
              'models': sorted(value.get('modelUsage') or {}), 'quota': value.get('api_error_status') == 429,
              'exit': code}
    _write(folder / 'result.json', result)
    return result


def run(batch, program, *, workers=4):
    """Launch every slot not yet launched; stop launching once the subscription reports its quota spent."""
    root = Path(batch).resolve(strict=True)
    pending = [slot for slot in _read(root / 'protocol.json')['slots'] if not (root / 'slots' / slot).exists()]
    spent = []

    def one(slot):
        if spent:
            return None
        result = execute(root, slot, program)
        if result['quota']:
            spent.append(slot)
        print(slot, result['state'], result['caught'], result['cost'], result['seconds'], flush=True)
        return result

    with ThreadPoolExecutor(workers) as pool:
        list(pool.map(one, pending))
    return spent


def collect(batch):
    root = Path(batch).resolve(strict=True)
    protocol = _read(root / 'protocol.json')
    results = [_read(root / 'slots' / slot / 'result.json') for slot in protocol['slots']
               if (root / 'slots' / slot / 'result.json').exists()]
    other = {}
    for result in results:
        if result['state'] != 'graded':
            other[result['state']] = other.get(result['state'], 0) + 1
    by_arm = {arm: [r for r in results if r['arm'] == arm] for arm in ARMS}
    return {'runs': {'scheduled': len(protocol['slots']), 'graded': sum(r['state'] == 'graded' for r in results),
                     'other': other, 'not_launched': len(protocol['slots']) - len(results)},
            'analysis': analyse(results), 'gate': protocol['gate'],
            'cost': {arm: round(sum(r['cost'] or 0 for r in rows), 4) for arm, rows in by_arm.items()},
            'mean_seconds': {arm: round(sum(r['seconds'] for r in rows) / len(rows), 1) if rows else None
                             for arm, rows in by_arm.items()},
            'mean_output_tokens': {arm: round(sum(r['output_tokens'] or 0 for r in rows) / len(rows)) if rows else None
                                   for arm, rows in by_arm.items()},
            'models': sorted({m for r in results for m in r['models']})}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    prepared = commands.add_parser('prepare')
    prepared.add_argument('--batch', type=Path, required=True)
    prepared.add_argument('--seeds', type=Path, required=True)
    prepared.add_argument('--manifest', type=Path, required=True)
    prepared.add_argument('--max-mutants', type=int)
    prepared.add_argument('--mutation-seconds', type=float)
    prepared.add_argument('--workers', type=int, default=4)
    launched = commands.add_parser('run')
    launched.add_argument('--batch', type=Path, required=True)
    launched.add_argument('--workers', type=int, default=4)
    collected = commands.add_parser('collect')
    collected.add_argument('--batch', type=Path, required=True)
    collected.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        limits = {key: value for key, value in (('max_mutants', args.max_mutants), ('seconds', args.mutation_seconds))
                  if value is not None}
        protocol, gate = prepare(args.batch, args.seeds, json.loads(args.manifest.read_text(encoding='utf-8')),
                                 limits=limits, workers=args.workers)
        print(len(protocol['slots']), 'slots;', 'gate', gate['tally'])
    elif args.action == 'run':
        program = shutil.which('claude')
        if not subscription.auth('claude', program, args.batch):
            parser.exit(2, 'claude is not signed in with a subscription\n')
        print('stopped on quota at', run(args.batch, [program], workers=args.workers) or 'nothing')
    else:
        summary = collect(args.batch)
        if args.out:
            _write(args.out, summary)
        print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
