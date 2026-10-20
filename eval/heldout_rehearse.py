"""No-model rehearsal of every held-out task on its own gold patch.

Before any paid run a task must fail at its base with no patch, resolve with
the fix's source change graded against the hidden tests, keep its answer out
of the interpreter's reach, and calibrate the vacuity probe in both
directions: the fix with its own tests is not VACUOUS, and the fix's source
alone is, because validation left the base suite green and the revert returns
to it. A task failing any of these is reported, never quietly replaced.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import time

from .bundle import GIT
from .heldout_env import canary
from .heldout_run import load_task
from .heldout_vacuity import vacuity
from .live import base_tree, grade_patch


def gold(task):
    """The fix commit as a patch, with and without the test files it changed."""
    source = task.source
    diff = [*GIT, '-C', source['repo'], 'diff', '--binary', source['base'], source['fix'], '--']
    # Bytes: a text pipe on Windows rewrites the newlines inside the patch.
    full = subprocess.run(diff, capture_output=True, check=True, timeout=180).stdout
    tests = [f':(exclude){path}' for path in source['hidden_files']]
    only = subprocess.run([*diff, '.', *tests], capture_output=True, check=True, timeout=180).stdout
    return full.decode('utf-8'), only.decode('utf-8')


def rehearse(task, work):
    started = time.monotonic()
    work = Path(work)
    work.mkdir(parents=True)
    full, only = gold(task)
    with tempfile.TemporaryDirectory() as neutral:
        value = {'canary': canary(task.source['python'], task.source['import_names'], neutral)}
    value['base_fails'] = grade_patch(task, '', work / 'grade-base').outcome == 'unfixed'
    value['gold_resolves'] = grade_patch(task, only, work / 'grade-gold').resolved
    base_tree(task, work / 'base')
    probe = dict(python=task.source['python'], env=task.source.get('env') or {}, test_dir=task.source['test_dir'])
    value['gold_vacuous'] = vacuity(work / 'base', full, work=work / 'vacuity-full', **probe)['vacuous']
    value['source_vacuous'] = vacuity(work / 'base', only, work=work / 'vacuity-source', **probe)['vacuous']
    value['usable'] = (value['canary'] and value['base_fails'] and value['gold_resolves']
                       and value['gold_vacuous'] is False and value['source_vacuous'] is True)
    value['seconds'] = round(time.monotonic() - started, 3)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True, help='outside any Git ancestor')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    corpus = json.loads(args.corpus.read_text(encoding='utf-8'))
    rows = {}
    for entry in corpus['tasks']:
        rows[entry['name']] = rehearse(load_task(corpus, entry['name']), args.work / entry['name'])
        args.out.write_text(json.dumps(rows, indent=2) + '\n', encoding='utf-8')
    usable = sum(row['usable'] for row in rows.values())
    print(usable, 'of', len(rows), 'tasks usable;', [name for name, row in rows.items() if not row['usable']])


if __name__ == '__main__':
    main()
