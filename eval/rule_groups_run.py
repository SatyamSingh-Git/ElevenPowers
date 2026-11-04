"""Does an agent act on a certified rule? One v3 stage per run, two arms that differ only
in elevenpowers.milestones.json.

Borrowed: the v3 runner's workspace, launch, seal, plugin checks, closed-book breach
detection and oracles (`eval.multistage_run`, `eval.multistage_oracles`). Added: a
simulated perfect certification, fixed in advance and frozen into the sealed protocol,
and a one-stage outcome. See docs/superpowers/specs/2026-11-04-rule-groups-acted-on-design.md.
"""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

from core.config import Config, save
from core.hosts.provenance import fingerprint
from core.hosts.setup import install
from core.milestones.propose import propose
from core.process import run, OutputLimitExceeded
from core.surface import TEST_NAME
from . import multistage_oracles as oracles
from . import subscription
from .heldout_run import _interpreter, _tool_calls
from .live import _sandboxed, _seed_git
from .multistage_cases import load, tree
from .multistage_run import (HARNESS as V3_HARNESS, KEPT_OUT, MARK, PROJECT_SETTINGS, SUPERPOWERS, TOOL_ROOT,
                             UNATTENDED, _breaches, _events, _files, _frozen, _hash, command)
from .preservation import _read, _write

ARMS = ('control', 'rules')
# The certified rules again, each description replaced by a reviewer's sentence.
DESCRIBED = 'described'
PROPOSALS = 50
CASES = TOOL_ROOT / 'eval' / 'multistage_v3'
MANIFEST = TOOL_ROOT / 'results' / 'multistage-v3' / 'manifest.json'
HARNESS = (*V3_HARNESS, 'eval/rule_groups_run.py')


def _harness():
    return _hash(b''.join((TOOL_ROOT / name).read_bytes() for name in HARNESS))


def _sources(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in Path(root).rglob('*.py')
            if not TEST_NAME.search(p.relative_to(root).as_posix())}


def breaking_pairs(case, scratch):
    """Every (file a stage's reference changes, that stage's declared dependent) pair."""
    scratch = Path(scratch)
    pairs = set()
    for n, stage in enumerate(case['stages'], 1):
        for which, quiet in enumerate(stage.get('quiet') or []):
            before = _sources(tree(case, n - 1, scratch / f'{n}-{which}-before'))
            after = _sources(tree(case, n, scratch / f'{n}-{which}-after', 'quiet', which))
            pairs |= {frozenset((path, quiet['file'])) for path in after
                      if before.get(path) != after[path] and path != quiet['file']}
    return pairs


def certify(case, scratch):
    """A perfect reviewer of the top proposals at stage 0: accept exactly the pairs some stage breaks."""
    scratch = Path(scratch)
    start = tree(case, 0, scratch / 'start')
    subprocess.run(['git', 'init', '-q'], cwd=start, check=True)
    subprocess.run(['git', 'add', '-A'], cwd=start, check=True, capture_output=True)
    wanted = breaking_pairs(case, scratch / 'pairs')
    entries = []
    for proposal in propose(start, limit=PROPOSALS, seconds=120)['proposals']:
        if frozenset(proposal['files']) in wanted:
            entries.append({**proposal['entry'],
                            'description': f"These files keep the same rule (they share {', '.join(proposal['shared'][:3])}).",
                            'checks': [{'kind': 'test_suite', 'command': f"python -m pytest {case['test_dir']} -q"}]})
    return entries


def outcome(case, stage, before, after):
    previous = oracles.groups(case, stage - 1, before)
    current = oracles.groups(case, stage, after)
    lost = oracles.regressions(case, stage, previous, current)
    fails = {name for quiet in case['stages'][stage - 1].get('quiet') or [] for name in quiet.get('fails', [])}
    return {'lost': lost, 'dependent_lost': bool(set(lost) & fails), 'groups': current}


def workspace(case, stage, arm, folder, entries):
    """The reference tree before `stage`, set up as the v3 ElevenPowers arm; `rules` adds the declarations."""
    if arm not in (*ARMS, DESCRIBED):
        raise ValueError(f'unknown arm {arm}')
    folder = Path(folder)
    work = tree(case, stage - 1, folder / 'work')
    _write(work / '.claude' / 'settings.json', PROJECT_SETTINGS)
    _interpreter(sys.executable, folder)
    save(work, Config(profile='guide', commands={'tests': f"python -m pytest {case['test_dir']} -q"}))
    install('claude', work, sys.executable, TOOL_ROOT)
    if arm != 'control':
        _write(work / 'elevenpowers.milestones.json', {'schema': 1, 'milestones': entries})
    _seed_git(work)
    return work


def prepare(batch, stages, *, replicates, seconds=900, model='claude-sonnet-5-5', cases=CASES, manifest=MANIFEST,
            arms=ARMS, descriptions=None):
    """Seal the slots and the certified rules before any run; `stages` is a list of (case, stage).

    `descriptions` ({case: {rule id: sentence}}) is required by, and only by, the described arm."""
    if model not in subscription.SUPPORTED_MODELS['claude']:
        raise ValueError('unsupported subscription model')
    if len(set(arms)) != len(arms) or len(arms) < 2 or not set(arms) <= {*ARMS, DESCRIBED}:
        raise ValueError(f'arms must be two or more of {(*ARMS, DESCRIBED)}')
    if (DESCRIBED in arms) != (descriptions is not None):
        raise ValueError('the described arm needs descriptions, and descriptions need the described arm')
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
    names = sorted({name for name, _ in stages})
    rules = {}
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as scratch:
        for name in names:
            if _files(cases, name) != _frozen(frozen, name):
                raise ValueError(f'{name} differs from the frozen manifest')
            rules[name] = certify(load(Path(cases) / name), Path(scratch) / name)
    described = {}
    for name in names if descriptions is not None else []:
        given = descriptions.get(name, {})
        if set(given) != {e['id'] for e in rules[name]}:
            raise ValueError(f'{name}: descriptions must name exactly its certified rules')
        described[name] = [{**e, 'description': given[e['id']]} for e in rules[name]]
    slots = []
    for replicate in range(replicates):
        for index, (name, stage) in enumerate(stages):
            order = arms if (index + replicate) % 2 == 0 else arms[::-1]
            slots += [f'{name}--{stage}--{arm}--{replicate}' for arm in order]
    protocol = {'schema': 1, 'prepared_at': datetime.now(timezone.utc).isoformat(), 'host': 'claude',
                'model': model, 'effort': 'medium', 'seconds': seconds, 'replicates': replicates,
                'stages': [list(s) for s in stages], 'unattended': UNATTENDED,
                'cases_root': str(Path(cases).absolute()), 'manifest': str(Path(manifest).absolute()),
                'files': {name: _frozen(frozen, name) for name in names}, 'rules': rules,
                'arms': list(arms), 'described': described,
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
    name, stage, arm, _ = slot.split('--')
    if _files(protocol['cases_root'], name) != protocol['files'][name]:
        raise ValueError(f'{name} differs from the frozen manifest')
    return protocol, load(Path(protocol['cases_root']) / name), int(stage), arm


def execute(batch, slot, executable):
    root = Path(batch).resolve(strict=True)
    folder = root / slot
    if (folder / 'result.json').exists():
        raise ValueError('attempt already exists; never retry launched slots')
    protocol, case, stage, arm = verify(root, slot)
    session = protocol['sessions'][slot]
    record = {'schema': 1, 'slot': slot, 'case': case['id'], 'stage': stage, 'arm': arm, 'state': 'preflight',
              'cost': 0.0, 'seconds': 0.0}
    _write(folder / 'result.json', record)
    version = run([executable, '--version'], cwd=folder, timeout=10, shell=False)
    record['host_version'] = version.stdout.strip()[:100] if version.returncode == 0 else ''
    if not record['host_version'] or not subscription.auth('claude', executable, folder):
        record['state'] = 'authentication_or_host_unavailable'
        _write(folder / 'result.json', record)
        return record
    entries = protocol['described'][case['id']] if arm == DESCRIBED else protocol['rules'][case['id']]
    work = workspace(case, stage, arm, folder, entries)
    shutil.copytree(work, folder / 'before', ignore=shutil.ignore_patterns(*KEPT_OUT))
    environment = {**_sandboxed(folder), 'ANTHROPIC_DEFAULT_HAIKU_MODEL': protocol['model']}
    prompt = case['stages'][stage - 1]['request'] + '\n\n' + UNATTENDED
    record['prompt_sha256'] = _hash(prompt.encode())
    record['state'] = 'running'
    _write(folder / 'result.json', record)
    started = time.monotonic()
    try:
        done = run(command(executable, work, prompt, session, 1, protocol['model']), cwd=work,
                   timeout=protocol['seconds'], shell=False, env=environment)
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
    events = _events(output)
    calls, result = _tool_calls(output)
    record['observation'] = subscription.observation('claude', json.dumps(result) if result else '', diagnostic)
    record['cost'] = round(float(result.get('total_cost_usd') or 0), 6) if result else 0.0
    inits = [e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init']
    record['superpowers'] = bool(inits) and all(
        SUPERPOWERS in [p.get('source') for p in e.get('plugins', [])] for e in inits)
    record['elevenpowers'] = any(e.get('subtype') == 'hook_response' and MARK in str(e.get('output', ''))
                                 for e in events)
    record['breaches'] = _breaches(calls, protocol['cases_root'], protocol['manifest'])
    if state == 'returned':
        state = 'completed' if record['observation']['completed'] else 'host_incomplete'
        if record['observation']['models'] != [protocol['model']]:
            state = 'model_unqualified'
        elif result.get('session_id') != session:
            state = 'conversation_unqualified'
        elif not record['superpowers'] or not record['elevenpowers']:
            state = 'plugins_unqualified'
        elif record['breaches']:
            state = 'closed_book_breach'
    record['state'] = state
    shutil.copytree(work, folder / 'after', ignore=shutil.ignore_patterns(*KEPT_OUT))
    record['outcome'] = outcome(case, stage, folder / 'before', folder / 'after')
    declared = {p for entry in entries for p in entry['inputs']}
    ledger = work / '.elevenpowers' / 'ledger.json'
    briefed = json.loads(ledger.read_text(encoding='utf-8')).get('briefed', []) if ledger.exists() else []
    # Delivery: a declared file got the rule note, before an Edit or after a shell write.
    record['declared_files_briefed'] = sorted(declared & set(briefed)) if arm != 'control' else []
    _write(folder / 'result.json', record)
    return record


def _hypergeometric(k, total, n_rules, n_control):
    return math.comb(n_rules, k) * math.comb(n_control, total - k) / math.comb(n_rules + n_control, total)


def stratified_p(tables):
    """Exact one-sided conditional test that the rules arm loses fewer, over strata of
    (rules lost, rules runs, control lost, control runs)."""
    distribution, observed = {0: 1.0}, 0
    for rules_lost, n_rules, control_lost, n_control in tables:
        total = rules_lost + control_lost
        observed += rules_lost
        step = {k: _hypergeometric(k, total, n_rules, n_control)
                for k in range(max(0, total - n_control), min(total, n_rules) + 1)}
        merged = {}
        for a, pa in distribution.items():
            for b, pb in step.items():
                merged[a + b] = merged.get(a + b, 0) + pa * pb
        distribution = merged
    return min(1.0, sum(p for k, p in distribution.items() if k <= observed))


def collect(batch):
    """One row per scheduled slot; never-launched and unqualified slots are counted, not dropped."""
    root = Path(batch).resolve(strict=True)
    protocol = _read(root / 'protocol.json')
    rows = []
    for slot in protocol['slots']:
        name, stage, arm, replicate = slot.split('--')
        row = {'slot': slot, 'case': name, 'stage': int(stage), 'arm': arm, 'replicate': int(replicate),
               'state': 'not_launched', 'comparable': False, 'dependent_lost': None}
        path = root / slot / 'result.json'
        if path.exists():
            record = _read(path)
            row.update(state=record['state'], cost=record['cost'], seconds=record['seconds'],
                       comparable=record['state'] == 'completed' and 'outcome' in record,
                       dependent_lost=record.get('outcome', {}).get('dependent_lost'),
                       lost=record.get('outcome', {}).get('lost'),
                       declared_files_briefed=record.get('declared_files_briefed', []))
        rows.append(row)
    tables = []
    for name, stage in protocol['stages']:
        def count(arm, lost):
            return sum(r['comparable'] and r['dependent_lost'] is lost
                       for r in rows if (r['case'], r['stage'], r['arm']) == (name, stage, arm))
        tables.append((count('rules', True), count('rules', True) + count('rules', False),
                       count('control', True), count('control', True) + count('control', False)))
    usable = [t for t in tables if t[1] and t[3]]
    return {'rows': rows, 'tables': tables, 'p_one_sided': stratified_p(usable) if usable else None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('batch', type=Path)
    p.add_argument('--stage', action='append', required=True, help='CASE:STAGE, repeatable')
    p.add_argument('--replicates', type=int, required=True)
    p.add_argument('--seconds', type=int, default=900)
    p.add_argument('--arm', action='append', help=f'repeatable; default {" and ".join(ARMS)}')
    p.add_argument('--descriptions', type=Path, help='JSON {case: {rule id: sentence}} for the described arm')
    e = sub.add_parser('execute')
    e.add_argument('batch', type=Path)
    e.add_argument('slot')
    e.add_argument('--executable', default='claude')
    c = sub.add_parser('collect')
    c.add_argument('batch', type=Path)
    args = parser.parse_args(argv)
    if args.action == 'prepare':
        stages = [(item.split(':')[0], int(item.split(':')[1])) for item in args.stage]
        value = prepare(args.batch, stages, replicates=args.replicates, seconds=args.seconds,
                        arms=tuple(args.arm or ARMS),
                        descriptions=json.loads(args.descriptions.read_text(encoding='utf-8')) if args.descriptions else None)
        print(json.dumps({'slots': value['slots'], 'rules': {k: len(v) for k, v in value['rules'].items()}}, indent=2))
    elif args.action == 'execute':
        record = execute(args.batch, args.slot, args.executable)
        print(json.dumps({k: record.get(k) for k in ('slot', 'state', 'cost', 'seconds', 'declared_files_briefed')}
                         | {'dependent_lost': record.get('outcome', {}).get('dependent_lost')}))
    else:
        value = collect(args.batch)
        print(json.dumps({'tables': value['tables'], 'p_one_sided': value['p_one_sided'],
                          'states': [r['state'] for r in value['rows']]}, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
