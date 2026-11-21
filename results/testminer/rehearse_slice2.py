"""$0 rehearsal of TestMiner slice 2 on a held-out project.

charset_normalizer is annotated, has no runtime dependencies, has a real
command line (python -m charset_normalizer FILE…), and its prepared
environment has coverage.py. Record one real use of that command line, then
examine what it ran with --observed. Usage: rehearse_slice2.py. Writes
rehearsal_slice2.json and removes the project's .elevenpowers/ afterwards.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.testminer.observe import record
from core.testminer.runner import mine

ROOT = Path('E:/ep-installed/heldout/repos/charset_normalizer')
PYTHON = Path('E:/ep-installed/heldout/venvs/charset_normalizer/Scripts/python.exe')

os.environ['PYTHONPATH'] = 'src'
version = subprocess.run([str(PYTHON), '-c', 'import coverage, pytest; print(coverage.__version__, pytest.__version__)'],
                         capture_output=True, text=True).stdout.split()
head = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
try:
    status, observation = record(ROOT, [str(PYTHON), '-m', 'charset_normalizer', 'data/sample-arabic-1.txt',
                                        'data/sample-chinese.txt', 'data/sample-russian.txt'])
    result = mine(ROOT, observed=True, command=f'"{PYTHON}" -m pytest -q -p no:cacheprovider',
                  seconds=1800, limit=12, test_seconds=300)
finally:
    shutil.rmtree(ROOT / '.elevenpowers', ignore_errors=True)
summary = {
    'project': 'charset_normalizer', 'commit': head, 'coverage.py': version[0], 'pytest': version[1],
    'record': {'status': status, 'command': observation['command'], 'arguments': observation['arguments'],
               'files': len(observation['files']),
               'lines': sum(len(item['lines']) for item in observation['files'].values())},
    'issues': result['issues'],
    'functions': [{k: f[k] for k in ('path', 'name', 'line', 'verdict', 'reason', 'values')} | {'tests': len(f['tests'])}
                  for f in result['functions']],
}
Path(__file__).with_name('rehearsal_slice2.json').write_text(json.dumps(summary, indent=1), encoding='utf-8')
print(json.dumps(summary, indent=1))
