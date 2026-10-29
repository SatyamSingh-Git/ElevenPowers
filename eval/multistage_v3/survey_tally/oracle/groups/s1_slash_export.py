"""Stage 1: response CSV files written by surveytally separate chosen options with `/`."""
import csv
import json

from surveytally.cli.main import main
from surveytally.files.survey_file import load_survey
from surveytally.model.responses import Response
from surveytally.reports.responses_export import write_responses

SURVEY = {
    'id': 'event',
    'title': 'Event feedback',
    'questions': [
        {'id': 'sessions', 'type': 'multi', 'text': 'Which sessions did you attend?',
         'options': ['keynote', 'workshop', 'panel', 'social']},
        {'id': 'day', 'type': 'single', 'text': 'Which day?', 'options': ['mon', 'tue']},
    ],
}


def survey_file(tmp_path):
    path = tmp_path / 'event.json'
    path.write_text(json.dumps(SURVEY), encoding='utf-8')
    return path


def cells(path, column):
    with open(path, newline='', encoding='utf-8') as handle:
        return [row[column] for row in csv.DictReader(handle)]


def test_written_cells_use_slashes(tmp_path):
    survey = load_survey(survey_file(tmp_path))
    path = tmp_path / 'out.csv'
    write_responses(survey, [Response('A1', {'sessions': ('keynote', 'social')}), Response('A2', {'day': 'tue'})], path)
    assert cells(path, 'sessions') == ['keynote/social', '']


def test_exported_project_responses_use_slashes(tmp_path):
    folder = tmp_path / 'project'
    main(['init', str(folder), str(survey_file(tmp_path))])
    responses = tmp_path / 'responses.csv'
    responses.write_text('respondent,sessions,day\nA1,workshop/panel,mon\n', encoding='utf-8')
    assert main(['import', str(folder), str(responses)]) == 0
    out = tmp_path / 'out.csv'
    assert main(['export-responses', str(folder), str(out)]) == 0
    assert cells(out, 'sessions') == ['workshop/panel']
