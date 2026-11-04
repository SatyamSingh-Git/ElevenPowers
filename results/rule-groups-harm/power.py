"""Power of the harm test: 53 stages, the runner's exact stratified test with the arms swapped (rules lose more)."""
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from eval.rule_groups_run import stratified_p  # noqa: E402

STAGES = 53


def power(control, rules, per_arm, rng, sims):
    hits = 0
    for _ in range(sims):
        tables = []
        for _ in range(STAGES):
            c = sum(rng.random() < control for _ in range(per_arm))
            r = sum(rng.random() < rules for _ in range(per_arm))
            tables.append((c, per_arm, r, per_arm))
        hits += stratified_p(tables) < 0.05
    return hits / sims


rng = random.Random(1104)
for per_arm, sims in ((1, 2000), (2, 1000)):
    for control in (0.05, 0.10):
        cells = {f'{rules:.2f}': power(control, rules, per_arm, rng, sims)
                 for rules in (control, control + 0.10, control + 0.15, control + 0.20)}
        print(f'{per_arm} per arm, control harm rate {control:.2f}: power at rules rate {cells}')
