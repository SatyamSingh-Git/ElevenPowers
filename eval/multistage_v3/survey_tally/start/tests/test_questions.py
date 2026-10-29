import pytest

from surveytally.model.errors import SurveyError
from surveytally.model.questions import FreeText, MultipleChoice, Option, Scale, SingleChoice
from surveytally.model.survey import ScoreDefinition, Survey


def test_choice_question_rejects_repeated_codes():
    with pytest.raises(SurveyError, match='option a is listed twice'):
        SingleChoice('q1', 'Pick one', options=[Option('a', 'A'), Option('a', 'Again')])


def test_choice_question_needs_options():
    with pytest.raises(SurveyError, match='needs at least one option'):
        SingleChoice('q1', 'Pick one')


def test_max_choices_must_fit_the_options():
    with pytest.raises(SurveyError, match='between 1 and 2'):
        MultipleChoice('q1', 'Pick some', options=[Option('a', 'A'), Option('b', 'B')], max_choices=3)


def test_scale_labels_must_match_points():
    with pytest.raises(SurveyError, match='2 labels for 5 points'):
        Scale('q1', 'Rate', labels=('low', 'high'))


def test_scale_labels_fall_back_to_the_number():
    scale = Scale('q1', 'Rate', low=0, high=2, labels=('none', '', 'all'))
    assert [scale.label_for(point) for point in scale.points()] == ['none', '1', 'all']


def test_free_text_cannot_be_cross_tabulated():
    with pytest.raises(SurveyError, match='cannot be cross-tabulated'):
        FreeText('q1', 'Say something').categories()


def test_survey_rejects_scores_on_unknown_questions():
    question = Scale('q1', 'Rate')
    with pytest.raises(SurveyError, match='uses unknown question q2'):
        Survey('s', 'S', [question], [ScoreDefinition('total', 'sum', ('q1', 'q2'))])


def test_survey_looks_up_questions(customer_survey):
    assert customer_survey.question('ease').high == 5
    with pytest.raises(SurveyError, match='unknown question nope'):
        customer_survey.question('nope')
