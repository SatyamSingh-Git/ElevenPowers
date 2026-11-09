"""The mandate wording for every reviewed rule of a case, generated from the rule's two proposed
functions by one fixed sentence, so no description is written with knowledge of any stage.
Usage: describe.py <case> > descriptions.json"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from core.milestones.propose import propose  # noqa: E402
from eval.multistage_cases import load, tree  # noqa: E402
from eval.rule_groups_run import CASES, PROPOSALS  # noqa: E402

# The rule note keeps the first 200 characters of a description, so the whole sentence must fit.
MANDATE = "`{a}` ({fa}) and `{b}` ({fb}) must stay consistent: change both in the same task."


def main():
    name = sys.argv[1]
    accepted = json.loads((ROOT / 'results' / 'rule-gate' / 'accepted.json').read_text(encoding='utf-8'))[name]
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as scratch:
        start = tree(load(Path(CASES) / name), 0, Path(scratch) / 'start')
        subprocess.run(['git', 'init', '-q'], cwd=start, check=True)
        subprocess.run(['git', 'add', '-A'], cwd=start, check=True, capture_output=True)
        proposals = {p['entry']['id']: p for p in propose(start, limit=PROPOSALS, seconds=120)['proposals']}
    described = {}
    for rule in accepted:
        (fa, fb), (a, b) = proposals[rule]['files'], proposals[rule]['functions']
        described[rule] = MANDATE.format(a=a, fa=fa, b=b, fb=fb)
    print(json.dumps({name: described}, indent=1, sort_keys=True))


if __name__ == '__main__':
    main()
