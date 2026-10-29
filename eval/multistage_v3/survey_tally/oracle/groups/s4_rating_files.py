"""Stage 4: survey files may call scale questions `rating`, and those work end to end."""
import json

import pytest

from surveytally.files.csv_responses import read_responses
from surveytally.files.survey_file import load_survey
from surveytally.services.tally import frequencies
from surveytally.services.validation import validate

SURVEY = {
    'id': 'clinic',
    'title': 'Clinic visit',
    'questions': [
        {'id': 'wait', 'type': 'rating', 'text': 'How was the waiting time?', 'low': 1, 'high': 5},
        {'id': 'staff', 'type': 'rating', 'text': 'How were the staff?', 'preset': 'quality4'},
        {'id': 'visit', 'type': 'single', 'text': 'Visit type', 'options': ['checkup', 'urgent']},
    ],
}


def survey(tmp_path):
    path = tmp_path / 'clinic.json'
    path.write_text(json.dumps(SURVEY), encoding='utf-8')
    return load_survey(path)


def test_rating_questions_load(tmp_path):
    loaded = survey(tmp_path)
    assert loaded.question('wait').points() == [1, 2, 3, 4, 5]
    assert loaded.question('staff').label_for(4) == 'Excellent'


def test_rating_answers_import_validate_and_tally(tmp_path):
    loaded = survey(tmp_path)
    path = tmp_path / 'responses.csv'
    path.write_text('respondent,wait,staff,visit\nP1,2,4,checkup\nP2,5,3,urgent\nP3,6,4,checkup\nP4,4,,urgent\n',
                    encoding='utf-8')
    responses = read_responses(loaded, path)
    assert responses[0].answers == {'wait': 2, 'staff': 4, 'visit': 'checkup'}
    valid, issues = validate(loaded, responses)
    assert [issue.message for issue in issues] == ['wait: 6 is outside 1..5']
    tables = frequencies(loaded, valid)
    assert tables['wait'].mean == pytest.approx(11 / 3)
    assert tables['staff'].row(4).count == 1
