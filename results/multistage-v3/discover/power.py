"""Power of the acted-on design: five stages, n runs per arm per stage, a one-sided
exact stratified test (conditional, Mantel-Haenszel's statistic) of rules < control.
Baseline per stage from v3's ElevenPowers losses; the effect is a common odds ratio."""
import math
import random
import sys

BASE = {'household_budget 7': 5 / 5, 'recipe_box 4': 4 / 5, 'library_loans 1': 3 / 5,
        'payroll_lite 2': 2 / 5, 'parcelpost 5': 2 / 5}


def hyper(k, total, n_rules, n_control):
    """Probability that the rules arm holds k of `total` losses, given the margins."""
    return math.comb(n_rules, k) * math.comb(n_control, total - k) / math.comb(n_rules + n_control, total)


def p_value(tables):
    # Exact conditional test: convolve each stratum's hypergeometric for the rules arm's losses.
    dist = {0: 1.0}
    observed = 0
    for rules_lost, n_rules, control_lost, n_control in tables:
        total = rules_lost + control_lost
        observed += rules_lost
        low, high = max(0, total - n_control), min(total, n_rules)
        step = {k: hyper(k, total, n_rules, n_control) for k in range(low, high + 1)}
        dist = {a + b: dist.get(a + b, 0) + pa * pb for a, pa in dist.items() for b, pb in step.items()} \
            if len(dist) == 1 else _merge(dist, step)
    return sum(p for k, p in dist.items() if k <= observed)


def _merge(dist, step):
    merged = {}
    for a, pa in dist.items():
        for b, pb in step.items():
            merged[a + b] = merged.get(a + b, 0) + pa * pb
    return merged


def rate_under(odds_ratio, p):
    p = min(max(p, 0.02), 0.98)  # a 5 of 5 baseline is not a certainty
    odds = p / (1 - p) * odds_ratio
    return odds / (1 + odds)


def power(n, odds_ratio, trials=4000, seed=7):
    rng = random.Random(seed)
    hits = 0
    for _ in range(trials):
        tables = []
        for p in BASE.values():
            control = sum(rng.random() < min(max(p, 0.02), 0.98) for _ in range(n))
            rules = sum(rng.random() < rate_under(odds_ratio, p) for _ in range(n))
            tables.append((rules, n, control, n))
        hits += p_value(tables) < 0.05
    return hits / trials


if __name__ == '__main__':
    for n in (int(a) for a in (sys.argv[1:] or ['6', '10'])):
        for odds_ratio in (1.0, 0.5, 0.25, 0.1):
            pooled = sum(rate_under(odds_ratio, p) for p in BASE.values()) / len(BASE)
            print(f'n={n:2} per arm per stage  odds ratio {odds_ratio:<4}  rules-arm loss rate {pooled:.0%}  '
                  f'power {power(n, odds_ratio):.0%}')
