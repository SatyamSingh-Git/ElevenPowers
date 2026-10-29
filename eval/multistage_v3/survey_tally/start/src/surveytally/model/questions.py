"""The kinds of question a questionnaire can hold.

Each kind has a `type` name, which is what a survey file calls it.
"""
from dataclasses import dataclass, field

from .errors import SurveyError

DEFAULT_TEXT_LIMIT = 500


@dataclass(frozen=True)
class Option:
    code: str
    label: str


@dataclass
class Question:
    id: str
    text: str
    required: bool = False

    type = None

    def label_for(self, value):
        return str(value)

    def categories(self):
        """The values a cross-tabulation splits this question into, in questionnaire order."""
        raise SurveyError(f'{self.id}: {self.type} questions cannot be cross-tabulated')

    def to_dict(self):
        data = {'id': self.id, 'type': self.type, 'text': self.text}
        if self.required:
            data['required'] = True
        return data


@dataclass
class ChoiceQuestion(Question):
    options: list = field(default_factory=list)

    def __post_init__(self):
        if not self.options:
            raise SurveyError(f'{self.id}: a choice question needs at least one option')
        seen = set()
        for option in self.options:
            if option.code in seen:
                raise SurveyError(f'{self.id}: option {option.code} is listed twice')
            seen.add(option.code)

    def codes(self):
        return [option.code for option in self.options]

    def has_option(self, code):
        return any(option.code == code for option in self.options)

    def label_for(self, value):
        for option in self.options:
            if option.code == value:
                return option.label
        return str(value)

    def categories(self):
        return self.codes()

    def to_dict(self):
        data = super().to_dict()
        data['options'] = [{'code': option.code, 'label': option.label} for option in self.options]
        return data


@dataclass
class SingleChoice(ChoiceQuestion):
    type = 'single'


@dataclass
class MultipleChoice(ChoiceQuestion):
    max_choices: int | None = None

    type = 'multi'

    def __post_init__(self):
        super().__post_init__()
        if self.max_choices is not None and not 1 <= self.max_choices <= len(self.options):
            raise SurveyError(f'{self.id}: max_choices must be between 1 and {len(self.options)}')

    def to_dict(self):
        data = super().to_dict()
        if self.max_choices is not None:
            data['max_choices'] = self.max_choices
        return data


@dataclass
class Scale(Question):
    low: int = 1
    high: int = 5
    labels: tuple = ()

    type = 'scale'

    def __post_init__(self):
        if self.low >= self.high:
            raise SurveyError(f'{self.id}: the lowest point {self.low} must be below the highest {self.high}')
        if self.labels and len(self.labels) != self.high - self.low + 1:
            raise SurveyError(f'{self.id}: {len(self.labels)} labels for {self.high - self.low + 1} points')

    def points(self):
        return list(range(self.low, self.high + 1))

    def label_for(self, value):
        if self.labels and self.low <= value <= self.high and self.labels[value - self.low]:
            return self.labels[value - self.low]
        return str(value)

    def categories(self):
        return self.points()

    def to_dict(self):
        data = super().to_dict()
        data['low'] = self.low
        data['high'] = self.high
        if self.labels:
            data['labels'] = list(self.labels)
        return data


@dataclass
class FreeText(Question):
    max_length: int = DEFAULT_TEXT_LIMIT

    type = 'text'

    def __post_init__(self):
        if self.max_length < 1:
            raise SurveyError(f'{self.id}: max_length must be at least 1')

    def to_dict(self):
        data = super().to_dict()
        if self.max_length != DEFAULT_TEXT_LIMIT:
            data['max_length'] = self.max_length
        return data
