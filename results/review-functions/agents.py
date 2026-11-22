"""$0: ep_review --functions on agent-made changes from the held-out sweep.

For each held-out task whose prepared environment has coverage.py, the
first ordinary-arm run's work folder is copied, the agent's uncommitted
work is committed on top of the seed, and the change is reviewed against
the seed with --functions. Usage: agents.py. Writes rehearsal_agents.json.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.review import review

SWEEP = Path('E:/ep-installed/heldout-sweep')
CORPUS = json.loads(Path('E:/ep-installed/heldout/corpus.json').read_text(encoding='utf-8'))
GIT = ['git', '-c', 'user.name=r', '-c', 'user.email=r@r', '-c', 'core.autocrlf=false']


def has_coverage(python):
    return subprocess.run([python, '-c', 'import coverage'], capture_output=True).returncode == 0


rows = []
tasks = CORPUS['tasks'] if isinstance(CORPUS, dict) else CORPUS
for task in tasks:
    slot = SWEEP / f"{task['name']}--ordinary--0"
    result = json.loads((slot / 'result.json').read_text(encoding='utf-8')) if (slot / 'result.json').exists() else {}
    if not result.get('resolved') or not has_coverage(task['python']):
        continue
    with tempfile.TemporaryDirectory(prefix='ep-agent-review-') as folder:
        work = Path(folder) / 'work'
        shutil.copytree(slot / 'work', work, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
        subprocess.run([*GIT, 'add', '-A'], cwd=work, check=True)
        subprocess.run([*GIT, 'commit', '-qm', 'agent', '--allow-empty'], cwd=work, check=True)
        saved = dict(os.environ)
        os.environ.update(task.get('env', {}))
        try:
            report = review(work, 'HEAD~1', 'HEAD', command=f'"{task["python"]}" -m pytest -q -p no:cacheprovider',
                            timeout=600, functions=True, function_seconds=900, function_limit=10)
        finally:
            os.environ.clear()
            os.environ.update(saved)
    functions = report['functions'] or {}
    row = {'task': task['name'], 'vacuous_in_sweep': result.get('vacuous'), 'verdict': report['verdict'],
           'reason': report['reason'], 'undone': report['undone'], 'tests_changed': report['tests'],
           'state': functions.get('state'), 'issues': functions.get('issues'),
           'functions': [{k: f[k] for k in ('path', 'name', 'line', 'verdict', 'reason', 'values')}
                         | {'tests': len(f['tests'])} for f in functions.get('functions', [])]}
    rows.append(row)
    print(json.dumps(row), flush=True)
Path(__file__).with_name('rehearsal_agents.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
