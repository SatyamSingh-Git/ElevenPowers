"""The plan in README.md: run --propose on real projects, sort what fills the top 50, compare with
the v3 cases, and check co-change on ElevenPowers' own history.

Usage: measure.py <new scratch dir>. Writes measure.json next to this file and prints a summary."""
from collections import Counter
import io
from itertools import combinations
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from core.milestones.propose import TEST_NAME, propose  # noqa: E402
from eval.multistage_cases import load, tree  # noqa: E402

PACKAGES = ['attr', 'click', '_pytest', 'rich', 'sqlalchemy']
DUNDER = re.compile(r'^__\w+__$')


def kind(functions):
    a, b = functions
    if DUNDER.match(a) and DUNDER.match(b):
        return 'dunder'
    return 'same name' if a == b else 'different names'


def git_init(folder):
    subprocess.run(['git', 'init', '-q'], cwd=folder, check=True)
    subprocess.run(['git', 'add', '-A'], cwd=folder, check=True, capture_output=True)


def run_cli(project):
    started = time.monotonic()
    done = subprocess.run([sys.executable, str(ROOT / 'plugin' / 'bin' / 'ep_milestones.py'), '--project', str(project),
                           '--propose', '--json'], capture_output=True, text=True, encoding='utf-8')
    seconds = round(time.monotonic() - started, 2)
    value = json.loads(done.stdout) if done.returncode == 0 else {}
    return done.returncode, seconds, value, done.stderr[-500:]


def co_change(repo, pairs):
    log = subprocess.run(['git', 'log', '--diff-filter=M', '--name-only', '--format=%x00'], cwd=repo,
                         capture_output=True, text=True, encoding='utf-8', check=True).stdout
    commits = [set(filter(None, chunk.splitlines())) for chunk in log.split('\0')]
    commits = [c for c in commits if len(c) > 1]
    touched = {}
    for number, files in enumerate(commits):
        for path in files:
            touched.setdefault(path, set()).add(number)
    return [bool(touched.get(a, set()) & touched.get(b, set())) for a, b in pairs], len(commits)


def main():
    scratch = Path(sys.argv[1]).resolve()
    report = {'real': {}, 'v3': {}}
    site = Path(sysconfig.get_paths()['purelib'])
    projects = {}
    for name in PACKAGES:
        projects[name] = scratch / name
        shutil.copytree(site / name, scratch / name / 'src' / name, ignore=shutil.ignore_patterns('__pycache__'))
        git_init(scratch / name)
    projects['ElevenPowers'] = scratch / 'ElevenPowers'
    projects['ElevenPowers'].mkdir()
    archive = subprocess.run(['git', 'archive', '--format=tar', 'HEAD'], cwd=ROOT, capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        bundle.extractall(projects['ElevenPowers'], filter='data')
    git_init(projects['ElevenPowers'])

    for name, project in projects.items():
        code, seconds, value, stderr = run_cli(project)
        proposals = value.get('proposals', [])
        row = {'exit': code, 'seconds': seconds, 'coverage': value.get('coverage'), 'stderr': stderr if code else '',
               'kinds': Counter(kind(p['functions']) for p in proposals),
               'top10': [f"{p['files'][0]}::{p['functions'][0]} <-> {p['files'][1]}::{p['functions'][1]}"
                         for p in proposals[:10]]}
        if name == 'ElevenPowers':
            pairs = [tuple(p['files']) for p in proposals]
            row['co_changed'], commits = co_change(ROOT, pairs)
            files = sorted(p for p in subprocess.run(['git', 'ls-files', '*.py'], cwd=ROOT, capture_output=True,
                                                     text=True, check=True).stdout.splitlines()
                           if not TEST_NAME.search(p) and 'def ' in (ROOT / p).read_text(encoding='utf-8', errors='replace'))
            base, _ = co_change(ROOT, list(combinations(files, 2)))
            row['co_change'] = {'commits_modifying_two_or_more_files': commits,
                                'top50_co_changed': sum(row['co_changed']), 'top50': len(pairs),
                                'base_pairs': len(base), 'base_co_changed': sum(base),
                                'by_kind': {k: [sum(c for c, p in zip(row['co_changed'], proposals)
                                                    if kind(p['functions']) == k),
                                                sum(kind(p['functions']) == k for p in proposals)]
                                            for k in ('dunder', 'same name', 'different names')}}
        report['real'][name] = row
        print(name, json.dumps({k: row[k] for k in ('exit', 'seconds', 'kinds')}),
              (row.get('coverage') or {}).get('complete'), flush=True)

    reviewed = {r['case']: set(r['certified']) for r in
                json.loads((ROOT / 'results' / 'rule-groups-reviewed' / 'reviewed.json').read_text(encoding='utf-8'))}
    all_kinds, truth_kinds = Counter(), Counter()
    for folder in sorted(p for p in (ROOT / 'eval' / 'multistage_v3').iterdir() if (p / 'case.json').exists()):
        case = load(folder)
        start = tree(case, 0, scratch / 'v3' / case['id'])
        git_init(start)
        proposals = propose(start, limit=50, seconds=120)['proposals']
        all_kinds.update(kind(p['functions']) for p in proposals)
        truth = [p for p in proposals if p['entry']['id'] in reviewed[case['id']]]
        truth_kinds.update(kind(p['functions']) for p in truth)
        report['v3'][case['id']] = {'kinds': Counter(kind(p['functions']) for p in proposals),
                                    'truth': [[p['functions'], kind(p['functions'])] for p in truth]}
    report['v3_totals'] = {'top50': all_kinds, 'truth': truth_kinds}
    print('v3 top-50 kinds', dict(all_kinds), '| truth kinds', dict(truth_kinds))
    Path(__file__).with_name('measure.json').write_text(json.dumps(report, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
