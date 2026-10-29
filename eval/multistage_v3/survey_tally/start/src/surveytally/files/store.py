"""A project folder: one survey, the responses accepted for it and, once computed, their weights."""
import json
from pathlib import Path

from ..model.errors import ProjectError
from ..model.responses import Response
from .survey_file import load_survey, save_survey
from .weights_file import read_weights, write_weights

SURVEY_FILE = 'survey.json'
RESPONSES_FILE = 'responses.jsonl'
WEIGHTS_FILE = 'weights.csv'


class Project:
    def __init__(self, folder):
        self.folder = Path(folder)
        if not (self.folder / SURVEY_FILE).is_file():
            raise ProjectError(f'{self.folder} is not a project: {SURVEY_FILE} is missing')
        self._survey = None

    @classmethod
    def create(cls, folder, survey):
        folder = Path(folder)
        if (folder / SURVEY_FILE).exists():
            raise ProjectError(f'{folder} already holds a project')
        folder.mkdir(parents=True, exist_ok=True)
        save_survey(survey, folder / SURVEY_FILE)
        (folder / RESPONSES_FILE).write_text('', encoding='utf-8')
        return cls(folder)

    @property
    def survey(self):
        if self._survey is None:
            self._survey = load_survey(self.folder / SURVEY_FILE)
        return self._survey

    def responses(self):
        path = self.folder / RESPONSES_FILE
        if not path.exists():
            return []
        with path.open(encoding='utf-8') as handle:
            return [_decode(json.loads(line)) for line in handle if line.strip()]

    def add_responses(self, responses):
        with (self.folder / RESPONSES_FILE).open('a', encoding='utf-8') as handle:
            for response in responses:
                handle.write(json.dumps(_encode(response), ensure_ascii=False) + '\n')

    def replace_responses(self, responses):
        (self.folder / RESPONSES_FILE).write_text('', encoding='utf-8')
        self.add_responses(responses)

    def has_weights(self):
        return (self.folder / WEIGHTS_FILE).is_file()

    def weights(self):
        return read_weights(self.folder / WEIGHTS_FILE) if self.has_weights() else None

    def save_weights(self, weights):
        write_weights(weights, self.folder / WEIGHTS_FILE)

    def clear_weights(self):
        (self.folder / WEIGHTS_FILE).unlink(missing_ok=True)


def _encode(response):
    answers = {key: list(value) if isinstance(value, tuple) else value for key, value in response.answers.items()}
    record = {'respondent': response.respondent, 'answers': answers}
    if response.submitted:
        record['submitted'] = response.submitted
    if response.duration is not None:
        record['duration'] = response.duration
    return record


def _decode(record):
    answers = {key: tuple(value) if isinstance(value, list) else value for key, value in record['answers'].items()}
    return Response(record['respondent'], answers, record.get('submitted', ''), record.get('duration'))
