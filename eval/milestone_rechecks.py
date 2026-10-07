"""Frozen authored recommendation/cost controls; explicit, disposable, no model."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import time

from core.ledger import Ledger
from core.milestones import build
from .milestones import Producer, _command, _definition, _put

CORPUS = Path(__file__).with_name('milestone_recheck_cases.json')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grade(case, report):
    """Only labelled references are an oracle; fallback is not a positive lead."""
    linked, fallback = set(), set()
    for command in report['rechecks']['commands']:
        target = fallback if command['priority'] == 'fallback' else linked
        target.update(m['id'] for m in command['milestones'])
    required, negative = set(case['required']), set(case['negative'])
    return {'known_required': len(required), 'known_negatives': len(negative),
            'hits': sorted(required & linked), 'misses': sorted(required - linked),
            'false_leads': sorted(negative & linked),
            'fallback_retained': sorted((required - linked) & fallback),
            'unlabelled_leads': sorted(linked - required - negative),
            'coverage_complete': report['coverage']['complete'],
            'advice_available': report['rechecks']['state'] == 'available'}


def _reads(root, changed, repeats):
    samples = []
    report = None
    ledger = root / '.elevenpowers/ledger.json'
    for index in range(repeats):
        before = digest(ledger)
        # Alternate ordering to expose rather than hide warming/order effects.
        results = {}
        for advised in ((False, True) if index % 2 == 0 else (True, False)):
            started = time.monotonic()
            value = build(root, impact=advised, changed=[changed] if advised else None)
            results['advised' if advised else 'plain'] = (value, (time.monotonic() - started) * 1000)
        report = results['advised'][0]
        samples.append({'plain_ms': round(results['plain'][1], 3),
                        'advised_ms': round(results['advised'][1], 3),
                        'added_ms': round(results['advised'][1] - results['plain'][1], 3),
                        'graph_ms': report['impact']['timings']['graph_ms'],
                        'query_ms': report['impact']['timings']['query_ms'],
                        'ranking_ms': report['rechecks']['timings']['ranking_ms'],
                        'selected_files': report['coverage']['selected_files'],
                        'selected_bytes': report['coverage']['selected_bytes'],
                        'source_fingerprint': report['coverage']['source_fingerprint'],
                        'ledger_unchanged': before == digest(ledger)})
    return report, samples


def exercise(destination, *, case_ids=None, repeats=3):
    if type(repeats) is not int or not 1 <= repeats <= 5:
        raise ValueError('repeats must be an integer from 1 to 5')
    corpus_bytes = CORPUS.read_bytes()
    cases = json.loads(corpus_bytes)['cases']
    known = {c['id'] for c in cases}
    if case_ids is not None:
        if (not isinstance(case_ids, list) or not case_ids or
                any(not isinstance(i, str) or i not in known for i in case_ids) or
                len(case_ids) != len(set(case_ids))):
            raise ValueError('case_ids must be unique known cases')
        cases = [c for c in cases if c['id'] in case_ids]
    destination = Path(destination).absolute()
    destination.mkdir(parents=True, exist_ok=False)
    _put(destination, 'frozen-corpus.json', corpus_bytes.decode('utf-8'))
    node = shutil.which('node')
    # Node's real version/output is collected, not assumed from the executable name.
    node_version = None
    if node:
        node_version = subprocess.run([node, '--version'], capture_output=True, text=True, timeout=10).stdout.strip()
    value = {'schema': 1, 'corpus_sha256': hashlib.sha256(corpus_bytes).hexdigest(),
             'environment': {'python': platform.python_version(), 'platform': platform.platform(), 'node': node_version},
             'runtime_sources': {}, 'cases': [], 'qualified': True,
             'limits': ['Authored small projects; labelled references are not a complete dependency oracle.',
                        'No agent/model runs or measured incremental coding benefit.',
                        'Fallback retention is not a recovered relationship; missing paths remain misses.',
                        'Read-only local timings include cache/order effects; no installed-host overhead claim.',
                        'Whole-source receipt invalidation remains conservative.']}
    code_root = Path(__file__).resolve().parents[1]
    for relative in ('core/milestones', 'core/impact'):
        for source in sorted((code_root / relative).rglob('*.py')):
            value['runtime_sources'][source.relative_to(code_root).as_posix()] = digest(source)
    for case in cases:
        directory = destination / case['id']
        directory.mkdir()
        root = directory / 'project'
        root.mkdir()
        record = {'id': case['id'], 'partition': case['partition'], 'language': case['language'],
                  'case_sha256': hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest(),
                  'reads': [], 'runs': []}
        value['cases'].append(record)
        if case['language'] == 'node' and node is None:
            record.update(state='incomplete', issues=['Node unavailable; no attempts discarded'])
            value['qualified'] = False
            continue
        producer = Producer(directory)
        for path, text in case['sources'].items():
            _put(root, path, text)
        commands = {}
        for milestone in case['milestones']:
            name = milestone['test']
            commands[milestone['id']] = (producer.python(name) if case['language'] == 'python' else
                _command([node, '--test', '--test-reporter=tap', f'checks/{name}.test.mjs']))
        rows = [{'id': m['id'], 'description': 'Controller-owned fixed boundary expectations.',
                 'inputs': m['inputs'], 'checks': [{'kind': 'test_suite', 'command': commands[m['id']]}]}
                for m in case['milestones']]
        _definition(root, rows)
        frozen = {p.relative_to(root).as_posix(): digest(p) for p in (root / 'checks').rglob('*') if p.is_file()}
        record['frozen_checks'] = frozen
        Ledger(root=root, task='baseline').save()
        for phase in ('baseline', 'fault', 'equivalent'):
            if phase != 'baseline':
                _put(root, case['change'], case[phase])
                Ledger(root=root, task=phase).save()
            before, samples = _reads(root, case['change'], repeats)
            record['reads'] += [dict(s, phase=phase) for s in samples]
            if phase == 'fault':
                record['grade'] = grade(case, before)
                record['recommendations'] = before['rechecks']
                record['impact_issues'] = before['impact']['issues']
            attempts = []
            for milestone in case['milestones']:
                outcome = producer.execute(root, commands[milestone['id']],
                                           junit=milestone['test'] if case['language'] == 'python' else None)
                outcome.update(phase=phase, milestone=milestone['id'])
                expected_failure = phase == 'fault' and case['fault_expected'] and milestone['id'] in case['required']
                outcome['expected'] = 'assertion failure' if expected_failure else 'pass'
                outcome['matches_expectation'] = bool(outcome['qualified_failure'] if expected_failure else outcome['qualified_pass'])
                attempts.append(outcome)
            record[phase] = {'qualified': all(a['matches_expectation'] for a in attempts),
                             'before_states': {m['id']: m['state'] for m in before['milestones']},
                             'after_state': build(root)['state']}
        record['runs'] = producer.runs
        record['frozen_checks_unchanged'] = all(digest(root / p) == sha for p, sha in frozen.items())
        record['state'] = 'qualified' if (record['frozen_checks_unchanged'] and
            all(record[p]['qualified'] for p in ('baseline', 'fault', 'equivalent')) and
            all(s['ledger_unchanged'] for s in record['reads'])) else 'incomplete'
        value['qualified'] &= record['state'] == 'qualified'
        _put(destination, 'observations.json', json.dumps(value, indent=2) + '\n')
    # Always publish partial attempts, including an entirely unavailable language.
    _put(destination, 'observations.json', json.dumps(value, indent=2) + '\n')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    try:
        value = exercise(args.output, repeats=args.repeats)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(2, f'Recheck exercise failed: {error}\n')
    print(json.dumps({'qualified': value['qualified'], 'cases': [
        {'id': c['id'], 'state': c['state'], 'grade': c.get('grade')} for c in value['cases']]}, indent=2))
    return 0 if value['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
