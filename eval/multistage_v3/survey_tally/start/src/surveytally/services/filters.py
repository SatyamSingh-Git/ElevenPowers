"""Subgroups: keeping only the responses that match conditions such as `region=north`.

A condition is a question id, an operator and, except for `?`, a value:

    region=north          answered north (multiple choice: chose north)
    region=north,south    answered north or south
    region!=north         answered something other than north
    satisfaction>=4       scale answers compare as numbers: = != < <= > >=
    comments?             answered at all

Respondents who did not answer a question match no condition on it except `!=`.
"""
from dataclasses import dataclass
import operator
import re

from ..model.errors import SurveyError
from ..model.questions import ChoiceQuestion, Scale

CONDITION = re.compile(r'^\s*([\w.-]+)\s*(!=|>=|<=|=|<|>|\?)\s*(.*?)\s*$')
COMPARISONS = {
    '<': operator.lt,
    '<=': operator.le,
    '>': operator.gt,
    '>=': operator.ge,
}


@dataclass(frozen=True)
class Condition:
    question: str
    operator: str
    values: tuple = ()

    def matches(self, response):
        chosen = response.chosen(self.question)
        if self.operator == '?':
            return bool(chosen)
        if self.operator == '=':
            return any(value in self.values for value in chosen)
        if self.operator == '!=':
            return not any(value in self.values for value in chosen)
        compare = COMPARISONS[self.operator]
        return bool(chosen) and compare(chosen[0], self.values[0])

    def __str__(self):
        return f'{self.question}{self.operator}{",".join(str(value) for value in self.values)}'


def parse_condition(survey, text):
    match = CONDITION.match(text)
    if match is None:
        raise SurveyError(f'cannot read the condition {text!r}')
    question_id, operator_, value = match.groups()
    question = survey.question(question_id)
    if operator_ == '?':
        if value:
            raise SurveyError(f'{text!r}: ? takes no value')
        return Condition(question_id, operator_)
    if not value:
        raise SurveyError(f'{text!r}: no value to compare with')
    parts = tuple(part.strip() for part in value.split(','))
    if isinstance(question, Scale):
        if operator_ in COMPARISONS and len(parts) > 1:
            raise SurveyError(f'{text!r}: {operator_} compares with one value')
        return Condition(question_id, operator_, _points(question, parts, text))
    if not isinstance(question, ChoiceQuestion):
        raise SurveyError(f'{text!r}: free-text questions only support ?')
    if operator_ not in ('=', '!='):
        raise SurveyError(f'{text!r}: choice questions only support = and !=')
    for code in parts:
        if not question.has_option(code):
            raise SurveyError(f'{text!r}: {question_id} has no option {code}')
    return Condition(question_id, operator_, parts)


def _points(question, parts, text):
    try:
        points = tuple(int(part) for part in parts)
    except ValueError:
        raise SurveyError(f'{text!r}: {question.id} compares with whole numbers') from None
    for point in points:
        if not question.low <= point <= question.high:
            raise SurveyError(f'{text!r}: {point} is outside {question.low}..{question.high}')
    return points


def select(responses, conditions):
    """The responses matching every condition, in their original order."""
    return [response for response in responses if all(condition.matches(response) for condition in conditions)]
