"""Simulated power for multi-stage v2, analysed per case as the design fixes it.

Each case draws its own arm-A rate of lost groups (or stale facts) per
conversation, log-normal around the stated rate; arm B's is that rate times
`ratio`. Counts are Poisson. A case's difference is mean(A) - mean(B) over its
replicates, and the cases enter an exact two-sided Wilcoxon signed-rank test at
alpha 0.025, Holm's first step for the two co-primary outcomes.
"""
import argparse
import json
import math
import random


def exact_signed_rank(differences):
    """Two-sided, exact over every sign flip; tied magnitudes share their average rank."""
    values = sorted(abs(d) for d in differences if d)
    if not values:
        return 1.0
    doubled, i = [], 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and values[j + 1] == values[i]:
            j += 1
        doubled += [i + j + 2] * (j - i + 1)
        i = j + 1
    rank = dict(zip(values, doubled))
    observed = sum(rank[abs(d)] for d in differences if d > 0)
    counts = {0: 1}
    for r in doubled:
        step = dict(counts)
        for total, ways in counts.items():
            step[total + r] = step.get(total + r, 0) + ways
        counts = step
    centre = sum(doubled) / 2
    extreme = sum(ways for total, ways in counts.items() if abs(total - centre) >= abs(observed - centre))
    return min(1.0, extreme / 2 ** len(doubled))


def _poisson(rng, mean):
    limit, k, product = math.exp(-mean), 0, rng.random()
    while product > limit:
        k += 1
        product *= rng.random()
    return k


def power(*, cases, replicates, rate, ratio, heterogeneity, simulations, seed, alpha=0.025):
    if cases < 1 or replicates < 1 or simulations < 1 or rate <= 0 or ratio <= 0 or heterogeneity < 0:
        raise ValueError('invalid design')
    rng = random.Random(seed)
    rejected = 0
    for _ in range(simulations):
        differences = []
        for _ in range(cases):
            own = math.exp(math.log(rate) + rng.gauss(0, heterogeneity))
            a = sum(_poisson(rng, own) for _ in range(replicates)) / replicates
            b = sum(_poisson(rng, own * ratio) for _ in range(replicates)) / replicates
            differences.append(a - b)
        rejected += exact_signed_rank(differences) <= alpha
    return {'rejection_rate': rejected / simulations, 'cases': cases, 'replicates': replicates,
            'conversations': 2 * cases * replicates}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=int, nargs='+', default=[8, 12])
    parser.add_argument('--replicates', type=int, nargs='+', default=[2, 3])
    parser.add_argument('--rate', type=float, nargs='+', default=[0.1, 0.25, 0.5, 1.0, 2.0, 4.0])
    parser.add_argument('--ratio', type=float, nargs='+', default=[1.0, 0.5, 0.3])
    parser.add_argument('--heterogeneity', type=float, nargs='+', default=[0.5, 1.0])
    parser.add_argument('--simulations', type=int, default=2000)
    args = parser.parse_args()
    rows = [power(cases=c, replicates=r, rate=a, ratio=o, heterogeneity=h, simulations=args.simulations, seed=1)
            | {'rate': a, 'ratio': o, 'heterogeneity': h}
            for c in args.cases for r in args.replicates for a in args.rate for o in args.ratio
            for h in args.heterogeneity]
    print(json.dumps(rows, indent=1))


if __name__ == '__main__':
    main()
