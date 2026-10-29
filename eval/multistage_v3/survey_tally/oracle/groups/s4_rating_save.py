"""Stage 4: saved survey files call scale questions `rating`, including ones first loaded as `scale`."""
import json

from surveytally.cli.main import main
from surveytally.files.survey_file import load_survey, save_survey

OLD = {
    'id': 'clinic',
    'title': 'Clinic visit',
    'questions': [
        {'id': 'wait', 'type': 'scale', 'text': 'How was the waiting time?', 'low': 1, 'high': 5},
        {'id': 'visit', 'type': 'single', 'text': 'Visit type', 'options': ['checkup', 'urgent']},
    ],
}


def old_file(tmp_path):
    path = tmp_path / 'old.json'
    path.write_text(json.dumps(OLD), encoding='utf-8')
    return path


def types(path):
    return {question['id']: question['type'] for question in json.loads(path.read_text(encoding='utf-8'))['questions']}


def test_saving_writes_rating(tmp_path):
    path = tmp_path / 'saved.json'
    save_survey(load_survey(old_file(tmp_path)), path)
    assert types(path) == {'wait': 'rating', 'visit': 'single'}
    assert load_survey(path).question('wait').high == 5


def test_a_new_project_stores_rating(tmp_path):
    folder = tmp_path / 'project'
    assert main(['init', str(folder), str(old_file(tmp_path))]) == 0
    assert types(folder / 'survey.json')['wait'] == 'rating'
