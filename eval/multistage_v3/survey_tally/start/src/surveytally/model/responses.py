"""Responses: one respondent's answers to one questionnaire."""
from dataclasses import dataclass, field


@dataclass
class Response:
    """Answers are keyed by question id; a question left unanswered has no key.

    A single-choice answer is an option code, a multiple-choice answer a tuple
    of codes, a scale answer an int and a free-text answer a string.
    `submitted` is an ISO date (YYYY-MM-DD) or empty, `duration` the seconds
    the respondent took, when the source recorded it.
    """

    respondent: str
    answers: dict = field(default_factory=dict)
    submitted: str = ''
    duration: int | None = None

    def answer(self, question_id):
        return self.answers.get(question_id)

    def answered(self, question_id):
        return question_id in self.answers

    def chosen(self, question_id):
        """The answer as a tuple, so that single and multiple choice read alike."""
        value = self.answers.get(question_id)
        if value is None:
            return ()
        return value if isinstance(value, tuple) else (value,)
