"""Stage 6: ids that differ only in case are one respondent, so a later submission replaces an earlier one."""
import json

from surveytally.cli.main import main
from surveytally.files.store import Project

SURVEY = {
    'id': 'panel',
    'title': 'Panel wave',
    'questions': [{'id': 'shop', 'type': 'single', 'text': 'Where do you shop?', 'options': ['online', 'store']}],
}


def project(tmp_path):
    survey = tmp_path / 'panel.json'
    survey.write_text(json.dumps(SURVEY), encoding='utf-8')
    folder = tmp_path / 'project'
    main(['init', str(folder), str(survey)])
    return folder


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding='utf-8')
    return str(path)


def test_later_import_replaces_the_same_respondent(tmp_path):
    folder = project(tmp_path)
    main(['import', str(folder), write(tmp_path, 'one.csv', 'respondent,submitted,shop\nab12,2026-05-01,online\n')])
    main(['import', str(folder), write(tmp_path, 'two.csv', 'respondent,submitted,shop\nAB12,2026-05-03,store\n')])
    stored = Project(folder).responses()
    assert len(stored) == 1
    assert stored[0].answers == {'shop': 'store'}


def test_repeat_within_one_file_keeps_the_latest(tmp_path):
    folder = project(tmp_path)
    text = 'respondent,submitted,shop\nXy9,2026-05-04,store\nxy9,2026-05-02,online\nZZ1,2026-05-01,online\n'
    assert main(['import', str(folder), write(tmp_path, 'one.csv', text)]) == 0
    stored = {response.respondent.upper(): response.answers['shop'] for response in Project(folder).responses()}
    assert stored == {'XY9': 'store', 'ZZ1': 'online'}
