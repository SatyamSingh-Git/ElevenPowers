"""Stage 3: percentages in exported frequency tables round half up."""
import csv
import json

from surveytally.files.survey_file import load_survey
from surveytally.model.responses import Response
from surveytally.reports.export import export_frequencies
from surveytally.services.tally import frequencies

SURVEY = {
    'id': 'canteen',
    'title': 'Canteen',
    'questions': [{'id': 'meal', 'type': 'single', 'text': 'Usual meal', 'options': ['soup', 'salad', 'hot']}],
}


def tables(tmp_path, people):
    path = tmp_path / 'canteen.json'
    path.write_text(json.dumps(SURVEY), encoding='utf-8')
    responses = [Response(f'C{n}', {'meal': 'soup' if n == 0 else 'hot'}) for n in range(people)]
    return frequencies(load_survey(path), responses)


def test_csv_half_rounds_up(tmp_path):
    path = tmp_path / 'tables.csv'
    export_frequencies(tables(tmp_path, 8), path, decimals=0)
    with open(path, newline='', encoding='utf-8') as handle:
        percent = {row['option']: row['percent'] for row in csv.DictReader(handle)}
    assert percent['soup'] == '13'
    assert percent['hot'] == '88'


def test_markdown_half_rounds_up(tmp_path):
    path = tmp_path / 'tables.md'
    export_frequencies(tables(tmp_path, 16), path, format='markdown', decimals=1)
    text = path.read_text(encoding='utf-8')
    assert '6.3' in text
    assert '6.2' not in text
