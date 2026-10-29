"""Stage 2: CSV frequency exports have the columns question, option, count, weighted, percent."""
import csv
import json

from surveytally.cli.main import main
from surveytally.files.survey_file import load_survey
from surveytally.model.responses import Response
from surveytally.reports.export import export_frequencies
from surveytally.services.tally import frequencies

SURVEY = {
    'id': 'library',
    'title': 'Library users',
    'questions': [
        {'id': 'visits', 'type': 'single', 'text': 'How often do you visit?', 'options': ['weekly', 'monthly', 'rarely']},
        {'id': 'uses', 'type': 'multi', 'text': 'What do you use?', 'options': ['books', 'wifi', 'events']},
    ],
}
COLUMNS = ['question', 'option', 'count', 'weighted', 'percent']


def survey_file(tmp_path):
    path = tmp_path / 'library.json'
    path.write_text(json.dumps(SURVEY), encoding='utf-8')
    return path


def header(path):
    with open(path, newline='', encoding='utf-8') as handle:
        return next(csv.reader(handle))


def test_export_frequencies_columns(tmp_path):
    survey = load_survey(survey_file(tmp_path))
    responses = [Response('L1', {'visits': 'weekly', 'uses': ('books', 'wifi')}), Response('L2', {'visits': 'rarely'})]
    path = tmp_path / 'tables.csv'
    export_frequencies(frequencies(survey, responses), path)
    assert header(path) == COLUMNS


def test_cli_export_columns(tmp_path):
    folder = tmp_path / 'project'
    main(['init', str(folder), str(survey_file(tmp_path))])
    responses = tmp_path / 'responses.csv'
    responses.write_text('respondent,visits\nL1,weekly\nL2,monthly\n', encoding='utf-8')
    main(['import', str(folder), str(responses)])
    out = tmp_path / 'tables.csv'
    assert main(['export', str(folder), str(out)]) == 0
    assert header(out) == COLUMNS
