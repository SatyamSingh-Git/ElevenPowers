"""$0 rehearsal of ep_review --functions on real changes.

Six recent fix commits of charset_normalizer, each reviewed against its
parent, in the project's own prepared environment (coverage.py 7.16.2),
with PYTHONPATH=src as its tests need. Usage: rehearse.py. Writes
rehearsal.json.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.review import review

ROOT = Path('E:/ep-installed/heldout/repos/charset_normalizer')
PYTHON = Path('E:/ep-installed/heldout/venvs/charset_normalizer/Scripts/python.exe')
COMMITS = ['3985662', '45dc0e3', '8e8f8c7', 'f9f92be', '3c560f1', 'e52699e']

os.environ['PYTHONPATH'] = 'src'
rows = []
for commit in COMMITS:
    report = review(ROOT, f'{commit}^', commit, command=f'"{PYTHON}" -m pytest -q -p no:cacheprovider',
                    functions=True, function_seconds=900, function_limit=10)
    functions = report['functions'] or {}
    row = {'commit': commit, 'verdict': report['verdict'], 'reason': report['reason'],
           'pinning': len(report['pinning']), 'undone': report['undone'],
           'state': functions.get('state'), 'issues': functions.get('issues'),
           'functions': [{k: f[k] for k in ('path', 'name', 'line', 'verdict', 'reason', 'values')}
                         | {'tests': len(f['tests'])} for f in functions.get('functions', [])]}
    rows.append(row)
    print(json.dumps(row), flush=True)
Path(__file__).with_name('rehearsal.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
