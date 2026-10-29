"""Scores: one number per respondent built from several scale questions.

A survey file names the rule each score uses; rules are looked up by that name.
A rule receives the (question, answer) pairs a respondent answered and the
number of items in the score, and returns a value or None when the respondent
cannot be scored.
"""
from dataclasses import dataclass

from ..model.errors import ScoringError
from ..model.questions import Scale
from .weighting import weight_for

TOP_BOX_POINTS = 2
NPS_PROMOTER = 9
NPS_DETRACTOR = 6

RULES = {}


def rule(name):
    def register(function):
        RULES[name] = function
        return function
    return register


@rule('sum')
def total(pairs, items):
    """The sum of the answers, only when every item is answered."""
    if len(pairs) < items:
        return None
    return float(sum(value for _, value in pairs))


@rule('mean')
def mean(pairs, items):
    """The mean of the answered items."""
    if not pairs:
        return None
    return sum(value for _, value in pairs) / len(pairs)


@rule('top_box')
def top_box(pairs, items):
    """The share of answered items in the top two points of their scale, from 0 to 1."""
    if not pairs:
        return None
    top = sum(1 for question, value in pairs if value > question.high - TOP_BOX_POINTS)
    return top / len(pairs)


@rule('nps')
def net_promoter(pairs, items):
    """100 for a promoter, 0 for a passive, -100 for a detractor; the mean is the Net Promoter Score."""
    if items != 1:
        raise ScoringError(f'the nps rule takes exactly one question, not {items}')
    if not pairs:
        return None
    [(_, value)] = pairs
    if value >= NPS_PROMOTER:
        return 100.0
    if value <= NPS_DETRACTOR:
        return -100.0
    return 0.0


@dataclass
class ScoreResult:
    name: str
    title: str
    rule: str
    values: dict
    mean: float | None
    base: int


def check_definitions(survey):
    """Every problem with the survey's scores, as messages; an empty list means all can be computed."""
    problems = []
    for definition in survey.scores:
        if definition.rule not in RULES:
            problems.append(f'unknown scoring rule {definition.rule}')
        for item in definition.items:
            if not isinstance(survey.question(item), Scale):
                problems.append(f'score {definition.name}: {item} is not a scale question')
        if definition.rule == 'nps' and len(definition.items) != 1:
            problems.append(f'score {definition.name}: the nps rule takes exactly one question')
    return problems


def compute_scores(survey, responses, weights=None):
    """Every score the survey defines, keyed by name, in definition order."""
    return {definition.name: score(survey, definition, responses, weights) for definition in survey.scores}


def score(survey, definition, responses, weights=None):
    function = RULES.get(definition.rule)
    if function is None:
        raise ScoringError(f'unknown scoring rule {definition.rule}')
    questions = [survey.question(item) for item in definition.items]
    for question in questions:
        if not isinstance(question, Scale):
            raise ScoringError(f'score {definition.name}: {question.id} is not a scale question')
    values = {}
    for response in responses:
        pairs = [(question, response.answers[question.id]) for question in questions if response.answered(question.id)]
        values[response.respondent] = function(pairs, len(questions))
    scored = [(value, weight_for(weights, respondent)) for respondent, value in values.items() if value is not None]
    total_weight = sum(weight for _, weight in scored)
    average = sum(value * weight for value, weight in scored) / total_weight if total_weight else None
    return ScoreResult(definition.name, definition.title, definition.rule, values, average, len(scored))
