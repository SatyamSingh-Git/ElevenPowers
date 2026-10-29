"""Tallies, weights, scores, cross-tabulations, exported tables, wave comparison and the summary."""
import json

import pytest

from surveytally.files.csv_responses import read_responses
from surveytally.files.survey_file import load_survey
from surveytally.files.weights_file import read_weights
from surveytally.reports.compare import compare
from surveytally.reports.export import export_frequencies
from surveytally.reports.summary import summary
from surveytally.services.analysis import analyse
from surveytally.services.crosstab import crosstab
from surveytally.services.scoring import compute_scores
from surveytally.services.tally import frequencies

SURVEY = {
    'id': 'branch',
    'title': 'Branch survey',
    'questions': [
        {'id': 'region', 'type': 'single', 'text': 'Region', 'options': ['north', 'south', 'east']},
        {'id': 'contact', 'type': 'single', 'text': 'Preferred contact',
         'options': [{'code': 'phone', 'label': 'Phone'}, {'code': 'email', 'label': 'Email'},
                     {'code': 'post', 'label': 'Post'}]},
        {'id': 'channels', 'type': 'multi', 'text': 'Channels used', 'options': ['web', 'app', 'store']},
        {'id': 'satisfaction', 'type': 'scale', 'text': 'Satisfaction', 'low': 1, 'high': 5},
        {'id': 'recommend', 'type': 'scale', 'text': 'Would you recommend us?', 'preset': 'likely11'},
        {'id': 'comments', 'type': 'text', 'text': 'Comments'},
    ],
    'scores': [
        {'name': 'sat', 'rule': 'mean', 'items': ['satisfaction']},
        {'name': 'nps', 'rule': 'nps', 'items': ['recommend']},
    ],
}

WAVE_1 = (
    'respondent,region,contact,channels,satisfaction,recommend,comments\n'
    'r1,north,email,web,5,10,Good\n'
    'r2,north,email,web,4,9,\n'
    'r3,north,phone,app,4,7,\n'
    'r4,south,email,store,2,3,\n'
    'r5,south,email,web,3,8,\n'
    'r6,east,post,app,5,10,\n'
    'r7,east,phone,web,1,0,Slow\n'
    'r8,north,email,,4,9,\n'
)

WAVE_2 = (
    'respondent,region,contact,satisfaction\n'
    'r1,north,email,4\n'
    'r2,south,email,4\n'
    'r3,south,phone,3\n'
    'r4,south,email,2\n'
    'r5,south,post,5\n'
    'r6,east,post,5\n'
    'r7,east,phone,1\n'
    'r8,north,email,4\n'
)

PANEL_WEIGHTS = (
    'respondent,weight\n'
    'r1,0.5\nr2,0.5\nr3,0.5\nr8,0.5\n'
    'r4,1.5\nr5,1.5\nr6,1.5\nr7,1.5\n'
)


@pytest.fixture
def survey(tmp_path):
    path = tmp_path / 'branch.json'
    path.write_text(json.dumps(SURVEY), encoding='utf-8')
    return load_survey(path)


def responses_from(tmp_path, survey, name, text):
    path = tmp_path / name
    path.write_text(text, encoding='utf-8')
    return read_responses(survey, path)


def test_scale_questions_are_tallied_with_a_mean(tmp_path, survey):
    tables = frequencies(survey, responses_from(tmp_path, survey, 'wave1.csv', WAVE_1))
    satisfaction = tables['satisfaction']
    assert [row.code for row in satisfaction.rows] == [1, 2, 3, 4, 5]
    assert [row.count for row in satisfaction.rows] == [1, 1, 1, 3, 2]
    assert satisfaction.mean == pytest.approx(3.5)
    assert tables['recommend'].row(10).count == 2


def test_choice_questions_are_counted(tmp_path, survey):
    tables = frequencies(survey, responses_from(tmp_path, survey, 'wave1.csv', WAVE_1))
    region = tables['region']
    assert (region.row('north').count, region.row('south').count, region.row('east').count) == (4, 2, 2)
    assert region.row('north').percent == pytest.approx(50.0)
    assert tables['channels'].row('web').count == 4
    assert tables['channels'].missing == 1


def test_panel_weights_are_applied(tmp_path, survey):
    responses = responses_from(tmp_path, survey, 'wave1.csv', WAVE_1)
    weights_path = tmp_path / 'panel_weights.csv'
    weights_path.write_text(PANEL_WEIGHTS, encoding='utf-8')
    region = frequencies(survey, responses, read_weights(weights_path))['region']
    assert region.row('north').count == 4
    assert region.row('north').percent == pytest.approx(25.0)
    assert region.row('south').percent == pytest.approx(37.5)


def test_scores(tmp_path, survey):
    scores = compute_scores(survey, responses_from(tmp_path, survey, 'wave1.csv', WAVE_1))
    assert scores['sat'].mean == pytest.approx(3.5)
    assert scores['nps'].mean == pytest.approx(25.0)
    assert scores['nps'].base == 8


def test_crosstab_column_percentages(tmp_path, survey):
    tab = crosstab(survey, responses_from(tmp_path, survey, 'wave1.csv', WAVE_1), 'region', 'contact')
    assert tab.percent('north', 'email') == pytest.approx(60.0)
    assert tab.percent('east', 'post') == pytest.approx(100.0)


def test_exported_waves_can_be_compared(tmp_path, survey):
    first = tmp_path / 'wave1_tables.csv'
    second = tmp_path / 'wave2_tables.csv'
    export_frequencies(frequencies(survey, responses_from(tmp_path, survey, 'wave1.csv', WAVE_1)), first)
    export_frequencies(frequencies(survey, responses_from(tmp_path, survey, 'wave2.csv', WAVE_2)), second)
    changes = {(change.question, change.option): change for change in compare(first, second)}
    assert changes[('region', 'north')].before == pytest.approx(50.0)
    assert changes[('region', 'north')].after == pytest.approx(25.0)
    assert changes[('region', 'south')].points == pytest.approx(25.0)
    assert changes[('contact', 'post')].points == pytest.approx(12.5)


def test_summary_names_the_most_chosen_option(tmp_path, survey):
    results = analyse(survey, responses_from(tmp_path, survey, 'wave1.csv', WAVE_1))
    lines = summary(results).splitlines()
    [contact] = [line for line in lines if line.startswith('contact')]
    assert 'Email' in contact
    assert 'Phone' not in contact
    [region] = [line for line in lines if line.startswith('region')]
    assert 'north' in region
