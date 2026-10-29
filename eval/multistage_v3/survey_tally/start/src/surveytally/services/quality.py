"""Response quality checks: straightliners, respondents who skip most questions, and
questions that many people skip.

The checks flag responses for someone to look at; nothing is dropped automatically.
"""
from dataclasses import dataclass

from ..model.questions import Scale

MIN_STRAIGHTLINE_ITEMS = 4
MAX_SKIPPED_SHARE = 0.5


@dataclass(frozen=True)
class Flag:
    respondent: str
    reason: str

    def __str__(self):
        return f'{self.respondent}: {self.reason}'


def straightliners(survey, responses, min_items=MIN_STRAIGHTLINE_ITEMS):
    """Respondents who gave the same point to every scale question they answered, when that is at least `min_items`."""
    scales = [question for question in survey.questions if isinstance(question, Scale)]
    flags = []
    for response in responses:
        values = [response.answer(question.id) for question in scales if response.answered(question.id)]
        if len(values) >= min_items and len(set(values)) == 1:
            flags.append(Flag(response.respondent, f'gave {values[0]} to all {len(values)} scale questions'))
    return flags


def skippers(survey, responses, max_share=MAX_SKIPPED_SHARE):
    """Respondents who left more than `max_share` of the questions unanswered."""
    total = len(survey.questions)
    flags = []
    for response in responses:
        skipped = sum(1 for question in survey.questions if not response.answered(question.id))
        if skipped / total > max_share:
            flags.append(Flag(response.respondent, f'skipped {skipped} of {total} questions'))
    return flags


def item_nonresponse(survey, responses):
    """For every question, the share of responses without an answer."""
    if not responses:
        return {question.id: 0.0 for question in survey.questions}
    return {question.id: sum(1 for response in responses if not response.answered(question.id)) / len(responses)
            for question in survey.questions}


def quality_flags(survey, responses):
    """All flags, grouped by respondent in the order the responses came."""
    flags = straightliners(survey, responses) + skippers(survey, responses)
    order = {response.respondent: index for index, response in enumerate(responses)}
    return sorted(flags, key=lambda flag: order[flag.respondent])
