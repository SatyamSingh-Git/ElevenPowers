"""Freeze a multi-stage case set before any model call: hashes, analysis and pilot cases.

    python results/multistage/freeze.py > results/multistage/manifest.json
    python results/multistage/freeze.py --set v3 > results/multistage-v3/manifest.json

Every file of every case, the four modules that build and grade them and the
authoring brief are hashed as committed. The pilot cases are the two ids with
the smallest sha256 of the seed and the id, chosen before any outcome exists.
v3's pilot is its first two cases, written before any v3 run.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SEED = 'multistage-v2-pilot'
SETS = {
    'v2': {'cases': 'eval/multistage_cases', 'pilot': None, 'power': 'results/multistage/power.json',
           'modules': ['eval/multistage_cases.py', 'eval/multistage_oracles.py', 'eval/multistage_rehearse.py',
                       'eval/multistage_power.py', 'eval/multistage_cases/AUTHORING.md',
                       'eval/multistage_cases/conftest.py', 'results/multistage/power.json',
                       'results/multistage/freeze.py']},
    'v3': {'cases': 'eval/multistage_v3', 'pilot': ['gradebook', 'parcelpost'], 'power': 'results/multistage-v3/power.json',
           'modules': ['eval/multistage_cases.py', 'eval/multistage_oracles.py', 'eval/multistage_quiet.py',
                       'eval/multistage_rehearse.py', 'eval/multistage_run.py', 'eval/multistage_power.py',
                       'eval/subscription.py', 'eval/multistage_v3/AUTHORING.md', 'eval/multistage_v3/conftest.py',
                       'results/multistage/freeze.py']},
}


def _sha(path):
    # The committed blob, not the checkout: a CRLF clone must reproduce the same hashes.
    blob = subprocess.run(['git', '-C', str(ROOT), 'cat-file', 'blob', f'HEAD:{path}'], capture_output=True, check=True)
    return hashlib.sha256(blob.stdout).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--set', choices=SETS, default='v2')
    chosen = SETS[parser.parse_args(argv).set]
    dirty = subprocess.run(['git', '-C', str(ROOT), 'status', '--porcelain'], capture_output=True, text=True,
                           check=True).stdout
    if dirty:
        raise SystemExit(f'refusing to freeze a working tree with uncommitted changes:\n{dirty}')
    tracked = subprocess.run(['git', '-C', str(ROOT), 'ls-files', chosen['cases']], capture_output=True,
                             text=True, check=True).stdout.split()
    ids = sorted({Path(p).parts[2] for p in tracked if p.endswith('/case.json')})
    cases = {name: {p: _sha(p) for p in tracked if Path(p).parts[2] == name} for name in ids}
    order = sorted(ids, key=lambda name: hashlib.sha256(f'{SEED}\0{name}'.encode()).hexdigest())
    print(json.dumps({
        'schema': 1,
        'commit': subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], capture_output=True, text=True,
                                 check=True).stdout.strip(),
        'modules': {p: _sha(p) for p in chosen['modules']},
        'cases': {name: {'files': len(files),
                         'sha256': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
                         'file_sha256': files} for name, files in cases.items()},
        'pilot': ({'seed': SEED, 'cases': order[:2]} if chosen['pilot'] is None else
                  {'rule': 'the first two cases written, before any run of this set', 'cases': chosen['pilot']}),
        'analysis': {
            'unit': 'case; per-case mean over replicates of (superpowers - superpowers+ElevenPowers)',
            'co_primary': ['earlier groups lost (passed at the previous graded stage, not passed now), summed over '
                           'stages', 'stale documented facts at the end of each stage, summed over stages'],
            'test': 'two-sided exact Wilcoxon signed-rank over cases (eval.multistage_power.exact_signed_rank); '
                    'zero differences dropped and counted; Holm across the two co-primaries',
            'comparable': 'a conversation counts only if every stage was attempted and graded; others stay in the '
                          'scheduled denominator, reported missing, never zero',
            'layout': f"chosen after the pilot from {chosen['power']}: the largest affordable layout with "
                      'power >= 0.8 at ratio 0.5 at the pilot arm-A rate, else the cheapest, run as descriptive',
            'pilot_runs': 'excluded from the analysis; no case is dropped or replaced on its pilot result',
        },
    }, indent=1))


if __name__ == '__main__':
    main()
