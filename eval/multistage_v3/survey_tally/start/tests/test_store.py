import pytest

from surveytally.files.store import Project
from surveytally.model.errors import ProjectError
from surveytally.model.responses import Response


def test_responses_survive_a_round_trip(tmp_path, customer_survey):
    project = Project.create(tmp_path / 'p', customer_survey)
    responses = [
        Response('R1', {'contact': 'email', 'channels': ('web', 'app'), 'ease': 4}, '2026-03-01', 200),
        Response('R2', {'comments': 'Fine'}),
    ]
    project.add_responses(responses)
    assert Project(tmp_path / 'p').responses() == responses


def test_replacing_responses_drops_the_old_ones(tmp_path, poll_survey):
    project = Project.create(tmp_path / 'p', poll_survey)
    project.add_responses([Response('R1', {'region': 'north'})])
    project.replace_responses([Response('R2', {'region': 'south'})])
    assert [response.respondent for response in project.responses()] == ['R2']


def test_a_folder_without_a_survey_is_not_a_project(tmp_path):
    with pytest.raises(ProjectError, match='survey.json is missing'):
        Project(tmp_path)


def test_weights_are_kept_until_cleared(tmp_path, poll_survey):
    project = Project.create(tmp_path / 'p', poll_survey)
    assert project.weights() is None
    project.save_weights({'R1': 1.25, 'R2': 0.75})
    assert project.weights() == {'R1': 1.25, 'R2': 0.75}
    project.clear_weights()
    assert project.weights() is None
