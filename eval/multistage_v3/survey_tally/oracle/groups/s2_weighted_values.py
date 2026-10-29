"""Stage 2: the weighted column holds the weighted count to one decimal, or the count without weights."""
import csv
import json

import pytest

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
RESPONSES = [
    Response('L1', {'visits': 'weekly', 'uses': ('books', 'wifi')}),
    Response('L2', {'visits': 'weekly', 'uses': ('wifi',)}),
    Response('L3', {'visits': 'monthly', 'uses': ('events', 'books')}),
    Response('L4', {'visits': 'rarely'}),
]
WEIGHTS = {'L1': 0.4, 'L2': 2.3, 'L3': 1.1, 'L4': 0.2}


def exported(tmp_path, weights):
    survey_path = tmp_path / 'library.json'
    survey_path.write_text(json.dumps(SURVEY), encoding='utf-8')
    path = tmp_path / 'tables.csv'
    export_frequencies(frequencies(load_survey(survey_path), RESPONSES, weights), path)
    with open(path, newline='', encoding='utf-8') as handle:
        return {(row['question'], row['option']): row for row in csv.DictReader(handle)}


def test_weighted_counts(tmp_path):
    rows = exported(tmp_path, WEIGHTS)
    assert float(rows[('visits', 'weekly')]['weighted']) == pytest.approx(2.7, abs=0.051)
    assert float(rows[('visits', 'monthly')]['weighted']) == pytest.approx(1.1, abs=0.051)
    assert float(rows[('uses', 'wifi')]['weighted']) == pytest.approx(2.7, abs=0.051)
    assert float(rows[('uses', 'books')]['weighted']) == pytest.approx(1.5, abs=0.051)
    assert rows[('visits', 'weekly')]['count'] == '2'


def test_without_weights_the_weighted_count_is_the_count(tmp_path):
    rows = exported(tmp_path, None)
    assert float(rows[('visits', 'weekly')]['weighted']) == 2
    assert float(rows[('uses', 'events')]['weighted']) == 1
    assert float(rows[('visits', 'rarely')]['weighted']) == 1
