"""Does the project's own test suite execute each lost dependent's file? A $0 feasibility check."""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

rows = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
rerun = set(json.loads(pathlib.Path('E:/ElevenPowers/results/multistage-v3/full-rerun-c.json').read_text(encoding='utf-8')))
out = []
for row in rows:
    batch = 'c' if row['slot'] in rerun else 'b'
    case = json.loads(pathlib.Path(f"E:/ElevenPowers/eval/multistage_v3/{row['slot'].split('--')[0]}/case.json").read_text(encoding='utf-8'))
    before = pathlib.Path(f"E:/ep-runs/multistage-v3-full-2026-10-30-{batch}/{row['slot']}/snapshots/{row['stage'] - 1}")
    with tempfile.TemporaryDirectory() as work:
        tree = pathlib.Path(work) / 'tree'
        shutil.copytree(before, tree)
        env = {**os.environ, 'PYTHONPATH': str(tree / case['pythonpath']), 'PYTHONDONTWRITEBYTECODE': '1'}
        subprocess.run([sys.executable, '-m', 'coverage', 'run', '--source', case['pythonpath'], '-m', 'pytest',
                        case['test_dir'], '-q', '-p', 'no:cacheprovider'], cwd=tree, env=env, capture_output=True,
                       timeout=300)
        report = subprocess.run([sys.executable, '-m', 'coverage', 'json', '-o', '-'], cwd=tree, env=env,
                                capture_output=True, text=True)
        files = json.loads(report.stdout or '{}').get('files', {})
        covered = {pathlib.PurePath(k).as_posix(): v['summary']['percent_covered'] for k, v in files.items()}
    for dependent in row['dependent']:
        out.append({'slot': row['slot'], 'stage': row['stage'], 'dependent': dependent,
                    'executed_percent': covered.get(dependent)})
        print(row['slot'], row['stage'], dependent, covered.get(dependent), flush=True)
pathlib.Path(sys.argv[2]).write_text(json.dumps(out, indent=1), encoding='utf-8')
