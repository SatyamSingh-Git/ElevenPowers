"""$0 rehearsal of TestMiner on two held-out projects.

Each project runs twice: under its own prepared environment, which has no
coverage.py (the usual case), and under ElevenPowers' own interpreter, which
has pytest 9.1.1 and coverage.py 7.10.7. Both projects have no runtime
dependencies. Usage: rehearse.py. Writes rehearsal.json.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.testminer.runner import mine

REPOS = Path('E:/ep-installed/heldout/repos')
VENVS = Path('E:/ep-installed/heldout/venvs')
OWN = Path(sys.executable)
CASES = [
    ('cachetools', 'src/cachetools/keys.py', 'pytest -q -p no:cacheprovider', {'PYTHONPATH': 'src'}),
    ('more-itertools', 'more_itertools/recipes.py', 'unittest', {}),
]

rows = []
for project, path, runner, env in CASES:
    for label, python in (('own environment', VENVS / project / 'Scripts' / 'python.exe'), ('ElevenPowers interpreter', OWN)):
        saved = dict(os.environ)
        os.environ.update(env)
        try:
            result = mine(REPOS / project, paths=(path,), command=f'"{python}" -m {runner}',
                          seconds=900, limit=10, test_seconds=300)
        finally:
            os.environ.clear()
            os.environ.update(saved)
        summary = {'project': project, 'interpreter': label, 'issues': result['issues'],
                   'functions': [{k: f[k] for k in ('name', 'line', 'verdict', 'reason', 'tests')} for f in result['functions']]}
        rows.append(summary)
        print(json.dumps(summary), flush=True)
Path(__file__).with_name('rehearsal.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
