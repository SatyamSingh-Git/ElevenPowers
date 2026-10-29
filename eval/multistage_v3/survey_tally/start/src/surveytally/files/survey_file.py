"""Survey files: a questionnaire stored as JSON."""
import json
from pathlib import Path

from .._generated import SCALE_PRESETS, SCHEMA_VERSION
from ..model.errors import SurveyError, SurveyFileError
from ..model.questions import ChoiceQuestion, FreeText, MultipleChoice, Option, Scale, SingleChoice
from ..model.survey import ScoreDefinition, Survey

QUESTION_TYPES = {
    'single': SingleChoice,
    'multi': MultipleChoice,
    'scale': Scale,
    'text': FreeText,
}


def load_survey(path):
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as error:
        raise SurveyFileError(f'{path.name}: not valid JSON ({error.msg}, line {error.lineno})') from None
    return survey_from_dict(data, source=path.name)


def save_survey(survey, path):
    text = json.dumps(survey_to_dict(survey), indent=2, ensure_ascii=False)
    Path(path).write_text(text + '\n', encoding='utf-8')


def survey_to_dict(survey):
    data = {
        'schema': SCHEMA_VERSION,
        'id': survey.id,
        'title': survey.title,
        'questions': [question.to_dict() for question in survey.questions],
    }
    if survey.scores:
        data['scores'] = [_score_to_dict(score) for score in survey.scores]
    return data


def survey_from_dict(data, source='survey'):
    if not isinstance(data, dict):
        raise SurveyFileError(f'{source}: expected a JSON object')
    schema = data.get('schema', SCHEMA_VERSION)
    if schema > SCHEMA_VERSION:
        raise SurveyFileError(f'{source}: schema {schema} is newer than the supported {SCHEMA_VERSION}')
    for key in ('id', 'title', 'questions'):
        if key not in data:
            raise SurveyFileError(f'{source}: missing {key}')
    try:
        questions = [question_from_dict(item) for item in data['questions']]
        scores = [_score_from_dict(item) for item in data.get('scores', [])]
        return Survey(str(data['id']), data['title'], questions, scores)
    except SurveyError as error:
        raise SurveyFileError(f'{source}: {error}') from None


def question_from_dict(item):
    if 'id' not in item:
        raise SurveyError('a question has no id')
    kind = item.get('type')
    if kind not in QUESTION_TYPES:
        raise SurveyError(f'question {item["id"]} has unknown type {kind}')
    cls = QUESTION_TYPES[kind]
    fields = {'id': str(item['id']), 'text': item.get('text', ''), 'required': bool(item.get('required', False))}
    if issubclass(cls, ChoiceQuestion):
        fields['options'] = [_option(entry) for entry in item.get('options', [])]
    if cls is MultipleChoice and 'max_choices' in item:
        fields['max_choices'] = int(item['max_choices'])
    if cls is Scale:
        fields.update(_scale_fields(item))
    if cls is FreeText and 'max_length' in item:
        fields['max_length'] = int(item['max_length'])
    return cls(**fields)


def _option(entry):
    if isinstance(entry, str):
        return Option(entry, entry)
    code = str(entry['code'])
    return Option(code, entry.get('label', code))


def _scale_fields(item):
    if 'preset' in item:
        if item['preset'] not in SCALE_PRESETS:
            raise SurveyError(f'question {item["id"]} uses unknown scale preset {item["preset"]}')
        low, high, labels = SCALE_PRESETS[item['preset']]
        return {'low': low, 'high': high, 'labels': labels}
    fields = {key: int(item[key]) for key in ('low', 'high') if key in item}
    if 'labels' in item:
        fields['labels'] = tuple(item['labels'])
    return fields


def _score_from_dict(item):
    for key in ('name', 'rule', 'items'):
        if key not in item:
            raise SurveyError(f'a score is missing {key}')
    return ScoreDefinition(item['name'], item['rule'], tuple(item['items']), item.get('label', ''))


def _score_to_dict(score):
    data = {'name': score.name, 'rule': score.rule, 'items': list(score.items)}
    if score.label:
        data['label'] = score.label
    return data
