"""Stage 5: exported frequency tables list choice options in questionnaire order."""
import csv
import json

from surveytally.files.survey_file import load_survey
from surveytally.model.responses import Response
from surveytally.reports.export import export_frequencies
from surveytally.services.tally import frequencies

SURVEY = {
    'id': 'commute',
    'title': 'Commute',
    'questions': [
        {'id': 'mode', 'type': 'single', 'text': 'Main mode',
         'options': [{'code': 'walk', 'label': 'Walk'}, {'code': 'bike', 'label': 'Bike'},
                     {'code': 'bus', 'label': 'Bus'}, {'code': 'car', 'label': 'Car'}]},
    ],
}
RESPONSES = [Response('K1', {'mode': 'car'}), Response('K2', {'mode': 'car'}), Response('K3', {'mode': 'bus'}),
             Response('K4', {'mode': 'walk'}), Response('K5', {'mode': 'car'}), Response('K6', {'mode': 'bus'})]


def tables(tmp_path):
    path = tmp_path / 'commute.json'
    path.write_text(json.dumps(SURVEY), encoding='utf-8')
    return frequencies(load_survey(path), RESPONSES)


def test_csv_rows_in_questionnaire_order(tmp_path):
    path = tmp_path / 'tables.csv'
    export_frequencies(tables(tmp_path), path)
    with open(path, newline='', encoding='utf-8') as handle:
        options = [row['option'] for row in csv.DictReader(handle) if row['question'] == 'mode']
    assert options == ['walk', 'bike', 'bus', 'car']


def test_markdown_rows_in_questionnaire_order(tmp_path):
    path = tmp_path / 'tables.md'
    export_frequencies(tables(tmp_path), path, format='markdown')
    text = path.read_text(encoding='utf-8')
    positions = [text.index(f'| {label} |') for label in ('Walk', 'Bike', 'Bus', 'Car')]
    assert positions == sorted(positions)
