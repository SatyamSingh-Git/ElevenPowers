"""Weights that make the responses match known population shares.

Raking adjusts every respondent's weight one target question at a time, and
repeats until each question's weighted shares match its targets. Extreme
weights are then trimmed to lie between a floor and a cap. Weights average
about 1, so weighted counts stay close to the number of respondents.
"""
from dataclasses import dataclass

from ..model.errors import WeightingError
from ..model.questions import SingleChoice

DEFAULT_CAP = 5.0
DEFAULT_FLOOR = 0.2
MAX_ITERATIONS = 50
TOLERANCE = 1e-6


def weight_for(weights, respondent):
    """A respondent's weight; everyone weighs 1 when there are no weights."""
    if weights is None:
        return 1.0
    try:
        return weights[respondent]
    except KeyError:
        raise WeightingError(f'no weight for respondent {respondent}') from None


def compute_weights(survey, responses, targets, *, cap=DEFAULT_CAP, floor=DEFAULT_FLOOR):
    """Weights by respondent id, rounded to six decimals.

    `targets` maps question ids to the population share of each option code,
    as `read_targets` returns them.
    """
    if not responses:
        raise WeightingError('there are no responses to weight')
    if not 0 < floor < cap:
        raise WeightingError(f'the floor {floor} must be above 0 and below the cap {cap}')
    questions = [_target_question(survey, question_id, shares) for question_id, shares in targets.items()]
    weights = {response.respondent: 1.0 for response in responses}
    for _ in range(MAX_ITERATIONS):
        largest = max(_rake(weights, responses, question, targets[question.id]) for question in questions)
        if largest < TOLERANCE:
            break
    return {respondent: round(min(cap, max(floor, weight)), 6) for respondent, weight in weights.items()}


def _target_question(survey, question_id, shares):
    question = survey.question(question_id)
    if not isinstance(question, SingleChoice):
        raise WeightingError(f'{question_id}: only single-choice questions can be weighted, not {question.type}')
    for code in shares:
        if not question.has_option(code):
            raise WeightingError(f'{question_id}: target for unknown option {code}')
    return question


def _rake(weights, responses, question, shares):
    """Scale weights so the question's weighted shares match `shares`; returns the largest adjustment."""
    totals = dict.fromkeys(shares, 0.0)
    for response in responses:
        code = response.answer(question.id)
        if code is None:
            continue
        if code not in totals:
            raise WeightingError(f'{question.id}: no target for option {code}')
        totals[code] += weights[response.respondent]
    answered = sum(totals.values())
    factors = {}
    for code, share in shares.items():
        if share and not totals[code]:
            raise WeightingError(f'{question.id}: no respondents chose {code}, which has a target of {share}')
        factors[code] = share * answered / totals[code] if totals[code] else 1.0
    for response in responses:
        code = response.answer(question.id)
        if code is not None:
            weights[response.respondent] *= factors[code]
    return max(abs(factor - 1) for factor in factors.values())


def efficiency(weights):
    """Kish's weighting efficiency: the effective sample size as a share of the actual one."""
    values = list(weights.values())
    return sum(values) ** 2 / (len(values) * sum(value * value for value in values))


@dataclass(frozen=True)
class WeightSummary:
    respondents: int
    smallest: float
    largest: float
    mean: float
    effective_size: float
    trimmed: int


def describe(weights, cap=DEFAULT_CAP, floor=DEFAULT_FLOOR):
    """Summary figures for a set of weights; `trimmed` counts weights sitting at the cap or floor."""
    values = list(weights.values())
    return WeightSummary(
        respondents=len(values),
        smallest=min(values),
        largest=max(values),
        mean=sum(values) / len(values),
        effective_size=efficiency(weights) * len(values),
        trimmed=sum(1 for value in values if value in (cap, floor)),
    )
