"""Does the product's propose() reproduce the spike's coverage? The same 51
never-read dependents and controls, with core.milestones.propose in place of the
spike's scorer. The product reads files through the project's own source scan,
so each tree is made a Git repository first, as a user's project would be."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from core.milestones.propose import propose  # noqa: E402
from eval.multistage_cases import load, tree  # noqa: E402

KS = (10, 20, 50, 100)


def as_repository(folder):
    subprocess.run(['git', 'init', '-q'], cwd=folder, check=True)
    subprocess.run(['git', 'add', '-A'], cwd=folder, check=True, capture_output=True)
    return folder


def main():
    spike = {(r['case'], r['stage'], r['dependent']): r for r in
             json.loads((HERE / 'discover.json').read_text(encoding='utf-8')) if r['fresh']}
    scratch = Path(tempfile.mkdtemp(prefix='ep-propose-'))
    places, agree = [], 0
    try:
        for root in sorted((ROOT / 'eval' / 'multistage_v3').iterdir()):
            if not (root / 'case.json').exists():
                continue
            case = load(root)
            for n in sorted({s for (c, s, _) in spike if c == case['id']}):
                before = as_repository(tree(case, n - 1, scratch / f"{case['id']}-{n - 1}"))
                proposals = [set(p['files']) for p in propose(before, limit=max(KS), seconds=120)['proposals']]
                for (c, s, dependent), row in spike.items():
                    if (c, s) != (case['id'], n):
                        continue
                    place = next((i for i, pair in enumerate(proposals, 1)
                                  if dependent in pair and pair & set(row['edited'])), None)
                    places.append(place)
                    agree += place == row['place']
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    print(f'{len(places)} never-read dependents; product covered within K:',
          {k: sum(p is not None and p <= k for p in places) for k in KS},
          f'| same place as the spike: {agree} of {len(places)}')


if __name__ == '__main__':
    main()
