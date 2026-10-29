"""Stage 5: frequency tables from `frequencies` list choice options in questionnaire order."""
import json

from surveytally.files.survey_file import load_survey
from surveytally.model.responses import Response
from surveytally.services.tally import frequencies

SURVEY = {
    'id': 'commute',
    'title': 'Commute',
    'questions': [
        {'id': 'mode', 'type': 'single', 'text': 'Main mode', 'options': ['walk', 'bike', 'bus', 'car']},
        {'id': 'also', 'type': 'multi', 'text': 'Also used', 'options': ['walk', 'bike', 'bus', 'car']},
    ],
}
RESPONSES = [
    Response('K1', {'mode': 'car', 'also': ('bus', 'car')}),
    Response('K2', {'mode': 'car', 'also': ('car',)}),
    Response('K3', {'mode': 'bus', 'also': ('bike', 'car')}),
    Response('K4', {'mode': 'car'}),
]


def test_options_in_questionnaire_order(tmp_path):
    path = tmp_path / 'commute.json'
    path.write_text(json.dumps(SURVEY), encoding='utf-8')
    tables = frequencies(load_survey(path), RESPONSES)
    assert [row.code for row in tables['mode'].rows] == ['walk', 'bike', 'bus', 'car']
    assert [row.count for row in tables['mode'].rows] == [0, 0, 1, 3]
    assert [row.code for row in tables['also'].rows] == ['walk', 'bike', 'bus', 'car']
