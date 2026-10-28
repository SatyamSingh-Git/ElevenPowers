"""Late rules: how many points late work keeps.

A rule is called as rule(points, max_points, days_late, settings), with points
as exact fractions and settings the course's LateSettings, and returns the
points the student keeps. Rules never take a score below zero.
"""
from fractions import Fraction

from ..errors import UnknownLateRule
from .rounding import exact

LATE_RULES = {}


def late_rule(name):
    def register(rule):
        LATE_RULES[name] = rule
        return rule
    return register


def get_late_rule(name):
    try:
        return LATE_RULES[name]
    except KeyError:
        raise UnknownLateRule(name) from None


def days_late(due_day, submitted_day):
    if submitted_day is None:
        return 0
    return max(0, submitted_day - due_day)


@late_rule("none")
def no_penalty(points, max_points, days, settings):
    return points


@late_rule("per_day")
def per_day(points, max_points, days, settings):
    if days == 0:
        return points
    percent = min(exact(settings.per_day) * days, exact(settings.cap))
    return max(Fraction(0), points - max_points * percent / 100)
