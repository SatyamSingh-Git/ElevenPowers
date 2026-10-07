"""Explicit read-only evaluation of sealed upstream milestone relationships."""
import argparse
import json
from pathlib import Path
import statistics
import time

from core.export import write
from core.milestones import build
from .impact_benchmark import seal
from .milestone_rechecks import grade


def inspect(root, files):
    return seal(Path(root), files)


def evaluate(corpus, roots, *, repeats=3, seconds=30, checkpoint=None):
    if type(repeats) is not int or not 1 <= repeats <= 20:
        raise ValueError('repeats must be an integer between 1 and 20')
    if corpus.get('schema') != 1 or not isinstance(corpus.get('projects'), list):
        raise ValueError('unsupported corpus')
    result = {'schema': 1, 'state': 'incomplete', 'projects': [], 'cases': [],
              'limits': ['Selected known relationships, not population precision or coding benefit.',
                         'Commands are declarations; this evaluation executes no project checks.',
                         'Whole-project reads are paired sequentially, without native host launch.']}
    def save():
        if checkpoint is not None:
            checkpoint(result)
    save()
    for project in corpus['projects']:
        root = Path(roots[project['id']]).resolve(strict=True)
        qualification = inspect(root, project['files'])
        row = {'id': project['id'], 'seal': qualification, 'files': len(project['files']),
               'bytes': sum((root / p).stat().st_size for p in project['files'] if (root / p).is_file())}
        result['projects'].append(row)
        save()
        if not qualification['complete']:
            continue
        for case in (c for c in corpus['cases'] if c['project'] == project['id']):
            record = {'id': case['id'], 'project': project['id'], 'samples': [], 'state': 'incomplete'}
            result['cases'].append(record)
            save()
            for _ in range(repeats):
                sample = {'state': 'incomplete'}
                record['samples'].append(sample)
                save()
                start = time.monotonic()
                build(root, seconds=seconds)
                sample['plain_ms'] = round((time.monotonic() - start) * 1000, 3)
                start = time.monotonic()
                report = build(root, impact=True, changed=[case['query']], seconds=seconds)
                sample['advised_ms'] = round((time.monotonic() - start) * 1000, 3)
                sample['added_ms'] = round(sample['advised_ms'] - sample['plain_ms'], 3)
                sample['state'] = 'complete'
                record['grade'] = grade(case, report)
                record['coverage'] = report['coverage']
                record['commands'] = report['rechecks']['commands']
                save()
            record['state'] = 'complete'
            save()
        row['after_seal'] = inspect(root, project['files'])
        save()
    result['state'] = ('complete' if len(result['cases']) == len(corpus['cases'])
                       and all(p.get('after_seal', {}).get('complete') for p in result['projects'])
                       else 'incomplete')
    samples = [s for c in result['cases'] for s in c['samples'] if s['state'] == 'complete']
    if samples:
        result['cost'] = {'paired_reads': len(samples),
                          'median_added_ms': statistics.median(s['added_ms'] for s in samples),
                          'max_advised_ms': max(s['advised_ms'] for s in samples)}
    save()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus', type=Path, required=True)
    parser.add_argument('--roots', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    # Refuse replacement of an existing run; subsequent checkpoints are ours.
    write(args.output, json.dumps({'state': 'incomplete'}), force=False)
    evaluate(json.loads(args.corpus.read_text()), json.loads(args.roots.read_text()),
             repeats=args.repeats,
             checkpoint=lambda value: write(args.output, json.dumps(value, indent=2), force=True))


if __name__ == '__main__':
    main()
