"""Stage 3: percentages in exported cross-tabulations round half up too."""
import csv
import json

from surveytally.files.survey_file import load_survey
from surveytally.model.responses import Response
from surveytally.reports.export import export_crosstab
from surveytally.services.crosstab import crosstab

SURVEY = {
    'id': 'canteen',
    'title': 'Canteen',
    'questions': [
        {'id': 'meal', 'type': 'single', 'text': 'Usual meal', 'options': ['soup', 'salad', 'hot']},
        {'id': 'site', 'type': 'single', 'text': 'Site', 'options': ['hq', 'depot']},
    ],
}


def test_crosstab_cells_half_round_up(tmp_path):
    survey_path = tmp_path / 'canteen.json'
    survey_path.write_text(json.dumps(SURVEY), encoding='utf-8')
    survey = load_survey(survey_path)
    responses = [Response(f'H{n}', {'meal': 'soup' if n == 0 else 'hot', 'site': 'hq'}) for n in range(8)]
    responses += [Response(f'D{n}', {'meal': 'salad', 'site': 'depot'}) for n in range(2)]
    path = tmp_path / 'tab.csv'
    export_crosstab(crosstab(survey, responses, 'meal', 'site'), path, decimals=0)
    with open(path, newline='', encoding='utf-8') as handle:
        rows = {row[0]: row for row in csv.reader(handle)}
    assert rows['soup'][1] == '13'
    assert rows['hot'][1] == '88'
