"""Simulated power for vacuity by arm, analysed per task as B9 fixed it in advance.

Each task draws its own ordinary-arm vacuity propensity (logit-normal around the
stated rate); the assisted arm shifts that logit by log(odds_ratio). A run is
vacuous only if it resolved. Per task and arm, the vacuous fraction among resolved
runs is compared; tasks where the arms differ enter a two-sided exact sign test.
Replicates are never treated as independent tasks.
"""
import argparse
import json
import math
import random


def _sign_test(wins, losses):
    n = wins + losses
    if not n:
        return 1.0
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def _signed_rank(differences):
    """Two-sided Wilcoxon signed-rank, normal approximation with tie correction."""
    values = sorted((abs(d), d > 0) for d in differences)
    n = len(values)
    if n < 2:
        return 1.0
    positive, ties, i = 0.0, 0, 0
    while i < n:
        j = i
        while j + 1 < n and values[j + 1][0] == values[i][0]:
            j += 1
        rank = (i + j) / 2 + 1
        positive += rank * sum(sign for _, sign in values[i:j + 1])
        ties += (j - i + 1) ** 3 - (j - i + 1)
        i = j + 1
    variance = n * (n + 1) * (2 * n + 1) / 24 - ties / 48
    if variance <= 0:
        return 1.0
    z = (abs(positive - n * (n + 1) / 4) - 0.5) / math.sqrt(variance)
    return min(1.0, math.erfc(max(z, 0) / math.sqrt(2)))


def _fraction(rng, probability, resolve, replicates):
    resolved = vacuous = 0
    for _ in range(replicates):
        if rng.random() < resolve:
            resolved += 1
            vacuous += rng.random() < probability
    return vacuous / resolved if resolved else None


def power(*, tasks, replicates, vanilla_vacuity, odds_ratio, resolve, heterogeneity, simulations, seed, alpha=0.05,
          test='sign'):
    if (tasks < 1 or replicates < 1 or simulations < 1 or not 0 < vanilla_vacuity < 1 or odds_ratio <= 0
            or not 0 < resolve <= 1 or heterogeneity < 0 or test not in ('sign', 'signed-rank')):
        raise ValueError('invalid design')
    rng = random.Random(seed)
    base, shift = math.log(vanilla_vacuity / (1 - vanilla_vacuity)), math.log(odds_ratio)
    rejected, discordant = 0, 0
    for _ in range(simulations):
        differences = []
        for _ in range(tasks):
            logit = base + rng.gauss(0, heterogeneity)
            ordinary = _fraction(rng, 1 / (1 + math.exp(-logit)), resolve, replicates)
            assisted = _fraction(rng, 1 / (1 + math.exp(-(logit + shift))), resolve, replicates)
            if ordinary is None or assisted is None or ordinary == assisted:
                continue
            differences.append(ordinary - assisted)
        discordant += len(differences)
        p = (_sign_test(sum(d > 0 for d in differences), sum(d < 0 for d in differences)) if test == 'sign'
             else _signed_rank(differences))
        rejected += p <= alpha
    return {'rejection_rate': rejected / simulations, 'mean_discordant_tasks': discordant / simulations,
            'tasks': tasks, 'replicates': replicates, 'runs': 2 * tasks * replicates, 'test': test}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tasks', type=int, nargs='+', default=[16, 25, 40, 60])
    parser.add_argument('--replicates', type=int, nargs='+', default=[1, 2, 3])
    parser.add_argument('--odds-ratio', type=float, nargs='+', default=[1.0, 0.5, 0.31, 0.2])
    parser.add_argument('--vanilla-vacuity', type=float, default=0.22)
    parser.add_argument('--resolve', type=float, default=0.92)
    parser.add_argument('--heterogeneity', type=float, nargs='+', default=[0.5, 1.0])
    parser.add_argument('--simulations', type=int, default=2000)
    parser.add_argument('--test', choices=['sign', 'signed-rank'], default='sign')
    args = parser.parse_args()
    rows = [power(tasks=t, replicates=r, vanilla_vacuity=args.vanilla_vacuity, odds_ratio=o, resolve=args.resolve,
                  heterogeneity=h, simulations=args.simulations, seed=1, test=args.test) | {'odds_ratio': o, 'heterogeneity': h}
            for t in args.tasks for r in args.replicates for o in args.odds_ratio for h in args.heterogeneity]
    print(json.dumps(rows, indent=1))


if __name__ == '__main__':
    main()
