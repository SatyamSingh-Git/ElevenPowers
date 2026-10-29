"""Stage 8: `surveytally weight` trims weights at 3.0 by default."""
import json

import pytest

from surveytally.cli.main import main
from surveytally.files.store import Project

SURVEY = {
    'id': 'town',
    'title': 'Town survey',
    'questions': [{'id': 'age', 'type': 'single', 'text': 'Age group', 'options': ['young', 'middle', 'old']}],
}


def test_cli_weights_are_capped_at_3(tmp_path):
    survey = tmp_path / 'town.json'
    survey.write_text(json.dumps(SURVEY), encoding='utf-8')
    folder = tmp_path / 'project'
    main(['init', str(folder), str(survey)])
    responses = tmp_path / 'responses.csv'
    rows = ['T0,young'] + [f'T{n},middle' for n in range(1, 6)] + [f'T{n},old' for n in range(6, 10)]
    responses.write_text('respondent,age\n' + '\n'.join(rows) + '\n', encoding='utf-8')
    main(['import', str(folder), str(responses)])
    targets = tmp_path / 'targets.csv'
    targets.write_text('question,option,share\nage,young,0.4\nage,middle,0.3\nage,old,0.3\n', encoding='utf-8')
    assert main(['weight', str(folder), str(targets)]) == 0
    weights = Project(folder).weights()
    assert weights['T0'] == pytest.approx(3.0)
    assert max(weights.values()) == pytest.approx(3.0)
