"""Exact power of the described-against-template test on one stage: every outcome enumerated, the runner's
exact one-sided test (Fisher's, with one stratum) at alpha 0.05. The template rate is parcelpost 5's 3 of 10."""
from math import comb
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from eval.rule_groups_run import stratified_p  # noqa: E402


def binomial(n, k, p):
    return comb(n, k) * p ** k * (1 - p) ** (n - k)


def power(n, template, described):
    return sum(binomial(n, d, described) * binomial(n, t, template)
               for d in range(n + 1) for t in range(n + 1) if stratified_p([(d, n, t, n)]) < 0.05)


for n in (10, 20, 30):
    print(f'{n} per arm:', {f'{described:.2f}': round(power(n, 0.30, described), 3) for described in (0.30, 0.15, 0.10, 0.05, 0.0)})
