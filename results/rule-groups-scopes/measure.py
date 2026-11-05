"""The plan in README.md, for one version of the code.

Usage: measure.py <checkout> <label> <new scratch dir>
The checkout supplies core/ and the command; the cases and projects are the same for every label.
Writes measure-<label>.json next to this file. `before` was 7592cde; `after` was 7592cde with
candidate.diff applied."""
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CHECKOUT = Path(sys.argv[1]).resolve()
for folder in ('convention-spike', 'dataflow'):
    sys.path.insert(0, str(ROOT / 'results/multistage-v3' / folder))
sys.path.insert(0, str(CHECKOUT))
from core.milestones.propose import propose  # noqa: E402
from eval.multistage_cases import load, tree  # noqa: E402
from fresh import edits  # noqa: E402

PACKAGES = ['attr', 'click', '_pytest', 'rich', 'sqlalchemy']
# The real-project snapshot of ElevenPowers is the commit the plan was written at, for every label.
PLANNED = '7592cde'


def git_init(folder):
    subprocess.run(['git', 'init', '-q'], cwd=folder, check=True)
    subprocess.run(['git', 'add', '-A'], cwd=folder, check=True, capture_output=True)
    return folder


def place(proposals, edited, dependent):
    return next((n for n, p in enumerate(proposals, 1) if dependent in p['files'] and set(p['files']) & set(edited)
                 and p['files'][0] != p['files'][1]), None)


def main():
    label, scratch = sys.argv[2], Path(sys.argv[3]).resolve()
    rows = json.loads((ROOT / 'results/multistage-v3/discover/discover.json').read_text(encoding='utf-8'))
    report = {'checkout': str(CHECKOUT), 'v3': [], 'stage0': {}, 'real': {}}
    for folder in sorted(p for p in (ROOT / 'eval/multistage_v3').iterdir() if (p / 'case.json').exists()):
        case = load(folder)
        built = {}

        def at(n):
            if n not in built:
                built[n] = git_init(tree(case, n, scratch / 'v3' / f"{case['id']}-{n}"))
            return built[n]
        report['stage0'][case['id']] = {p['entry']['id']: p['files']
                                        for p in propose(at(0), limit=50, seconds=120)['proposals']}
        stages = case['stages']
        for n in sorted({r['stage'] for r in rows if r['case'] == case['id']}):
            proposals = propose(at(n - 1), limit=100, seconds=120)['proposals']
            # The control, as in the discover spike: another stage's changed files, the same proposals.
            other = next(m for m in (n + 1, n - 1, n + 2, n - 2) if 1 <= m <= len(stages) and m != n)
            changed = edits(at(other - 1), at(other))
            for r in rows:
                if (r['case'], r['stage']) == (case['id'], n):
                    report['v3'].append({**{k: r[k] for k in ('case', 'stage', 'dependent', 'kind', 'fresh')},
                                         'place': place(proposals, r['edited'], r['dependent']),
                                         'control': place(proposals, [p for p in changed if p != r['dependent']],
                                                          r['dependent'])})
        print(case['id'], flush=True)

    site = Path(sysconfig.get_paths()['purelib'])
    projects = {}
    for name in PACKAGES:
        projects[name] = scratch / 'real' / name
        shutil.copytree(site / name, projects[name] / 'src' / name, ignore=shutil.ignore_patterns('__pycache__'))
        git_init(projects[name])
    projects['ElevenPowers'] = scratch / 'real' / 'ElevenPowers'
    projects['ElevenPowers'].mkdir(parents=True)
    archive = subprocess.run(['git', 'archive', '--format=tar', PLANNED], cwd=ROOT, capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        bundle.extractall(projects['ElevenPowers'], filter='data')
    git_init(projects['ElevenPowers'])
    for name, project in projects.items():
        started = time.monotonic()
        done = subprocess.run([sys.executable, str(CHECKOUT / 'plugin/bin/ep_milestones.py'), '--project', str(project),
                               '--propose', '--json'], capture_output=True, text=True, encoding='utf-8')
        seconds = round(time.monotonic() - started, 2)
        value = json.loads(done.stdout) if done.returncode == 0 else {}
        report['real'][name] = {'exit': done.returncode, 'seconds': seconds, 'coverage': value.get('coverage'),
                                'stderr': done.stderr[-500:] if done.returncode else '',
                                'top50': [[p['files'], p['functions'], p['shared'], p['score']]
                                          for p in value.get('proposals', [])]}
        print(name, done.returncode, seconds, flush=True)
    (HERE / f'measure-{label}.json').write_text(json.dumps(report, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
