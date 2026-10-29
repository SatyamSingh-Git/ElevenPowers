"""Stage 8: compute_weights trims weights at 3.0 unless told otherwise."""
import json

import pytest

from surveytally.files.survey_file import load_survey
from surveytally.model.responses import Response
from surveytally.services.weighting import compute_weights

SURVEY = {
    'id': 'town',
    'title': 'Town survey',
    'questions': [{'id': 'age', 'type': 'single', 'text': 'Age group', 'options': ['young', 'middle', 'old']}],
}
TARGETS = {'age': {'young': 0.4, 'middle': 0.3, 'old': 0.3}}


def survey(tmp_path):
    path = tmp_path / 'town.json'
    path.write_text(json.dumps(SURVEY), encoding='utf-8')
    return load_survey(path)


def responses():
    groups = ['young'] * 1 + ['middle'] * 5 + ['old'] * 4
    return [Response(f'T{n}', {'age': group}) for n, group in enumerate(groups)]


def test_weights_are_capped_at_3(tmp_path):
    weights = compute_weights(survey(tmp_path), responses(), TARGETS)
    assert weights['T0'] == pytest.approx(3.0)
    assert max(weights.values()) == pytest.approx(3.0)
    assert weights['T1'] == pytest.approx(0.6, abs=1e-6)


def test_an_explicit_cap_still_wins(tmp_path):
    weights = compute_weights(survey(tmp_path), responses(), TARGETS, cap=4.5)
    assert weights['T0'] == pytest.approx(4.0)
