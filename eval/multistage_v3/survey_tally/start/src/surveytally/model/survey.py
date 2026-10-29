"""A questionnaire: its questions, in order, and the scores built from them."""
from dataclasses import dataclass, field

from .errors import SurveyError


@dataclass(frozen=True)
class ScoreDefinition:
    """A score combines answers to `items` with the scoring rule called `rule`."""

    name: str
    rule: str
    items: tuple
    label: str = ''

    @property
    def title(self):
        return self.label or self.name


@dataclass
class Survey:
    id: str
    title: str
    questions: list
    scores: list = field(default_factory=list)

    def __post_init__(self):
        self._by_id = {}
        for question in self.questions:
            if question.id in self._by_id:
                raise SurveyError(f'question {question.id} is defined twice')
            self._by_id[question.id] = question
        names = set()
        for score in self.scores:
            if score.name in names:
                raise SurveyError(f'score {score.name} is defined twice')
            names.add(score.name)
            if not score.items:
                raise SurveyError(f'score {score.name} has no items')
            for item in score.items:
                if item not in self._by_id:
                    raise SurveyError(f'score {score.name} uses unknown question {item}')

    def question(self, question_id):
        try:
            return self._by_id[question_id]
        except KeyError:
            raise SurveyError(f'unknown question {question_id}') from None

    def has_question(self, question_id):
        return question_id in self._by_id

    def question_ids(self):
        return [question.id for question in self.questions]

    def score(self, name):
        for score in self.scores:
            if score.name == name:
                return score
        raise SurveyError(f'unknown score {name}')
