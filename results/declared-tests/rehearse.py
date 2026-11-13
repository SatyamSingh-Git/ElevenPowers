"""$0 rehearsal of borrowing the test command a project declares in tox, make or CI.

Held-out projects: discovery before and after, then the new command run in the
project's prepared environment. Unrelated projects: discovery before and after
only, nothing executed. Usage: rehearse.py [CONTROL_DIR ...]
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core import test_command
from core.config import discover_commands

REPOS = Path('E:/ep-installed/heldout/repos')
VENVS = Path('E:/ep-installed/heldout/venvs')
ENV = {'charset_normalizer': {'PYTHONPATH': 'src'}}
corpus = json.loads(Path('E:/ElevenPowers/results/heldout/corpus.json').read_text(encoding='utf-8'))['tasks']
for task in corpus:
    ENV.setdefault(Path(task['repo']).name, task.get('env', {}))


def before_after(root):
    original = test_command.declared
    test_command.declared = lambda root: None
    try:
        before = discover_commands(root).get('tests')
    finally:
        test_command.declared = original
    origins = {}
    after = discover_commands(root, origins).get('tests')
    return before, after, origins.get('tests')


rows = []
for repo in sorted(p for p in REPOS.iterdir() if p.is_dir()):
    before, after, source = before_after(repo)
    row = {'project': repo.name, 'kind': 'held-out', 'before': before, 'after': after, 'source': source}
    if after and after != before:
        env = {**os.environ, **ENV.get(repo.name, {})}
        env['PATH'] = str(VENVS / repo.name / ('Scripts' if os.name == 'nt' else 'bin')) + os.pathsep + env['PATH']
        start = time.monotonic()
        done = subprocess.run(after, shell=True, cwd=repo, env=env, capture_output=True, text=True,
                              encoding='utf-8', errors='replace', timeout=600)
        tail = (done.stdout + done.stderr).strip().splitlines()[-1:] or ['']
        row.update(exit=done.returncode, seconds=round(time.monotonic() - start, 1), last=tail[0][:100])
    rows.append(row)
for folder in sys.argv[1:]:
    root = Path(folder)
    if (root / '.git').exists():
        before, after, source = before_after(root)
        rows.append({'project': root.name, 'kind': 'control', 'before': before, 'after': after, 'source': source})
for row in rows:
    print(json.dumps(row))
Path(__file__).with_name('rehearsal.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
