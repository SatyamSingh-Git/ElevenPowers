"""Scoring policies: how category results combine into one exact percent.

A policy takes the course's CategoryResults and returns a Fraction percent,
or None when no category has anything graded yet.
"""
from ..errors import UnknownPolicy


def weighted(results):
    graded = [result for result in results if result.graded]
    total_weight = sum(result.weight for result in graded)
    if not graded or total_weight == 0:
        return None
    return sum(result.weight * result.exact_percent for result in graded) / total_weight


def points_total(results):
    possible = sum(result.possible for result in results)
    if possible == 0:
        return None
    return sum(result.earned for result in results) / possible * 100


POLICIES = {
    "weighted": weighted,
    "points": points_total,
}


def get_policy(name):
    try:
        return POLICIES[name]
    except KeyError:
        raise UnknownPolicy(name, list(POLICIES)) from None
