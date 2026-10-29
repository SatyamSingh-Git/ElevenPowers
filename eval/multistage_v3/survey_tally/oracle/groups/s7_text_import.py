"""Stage 7: long open-ended answers in an imported response file are accepted."""
import csv
import json

from surveytally.cli.main import main
from surveytally.files.store import Project

SURVEY = {
    'id': 'feedback',
    'title': 'Open feedback',
    'questions': [
        {'id': 'story', 'type': 'text', 'text': 'Tell us what happened'},
        {'id': 'overall', 'type': 'single', 'text': 'Overall', 'options': ['good', 'bad']},
    ],
}


def test_import_keeps_a_1500_character_answer(tmp_path):
    survey = tmp_path / 'feedback.json'
    survey.write_text(json.dumps(SURVEY), encoding='utf-8')
    responses = tmp_path / 'responses.csv'
    with responses.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['respondent', 'story', 'overall'])
        writer.writerow(['F1', 'word ' * 300, 'good'])
        writer.writerow(['F2', 'short', 'bad'])
    assert main(['validate', str(survey), str(responses)]) == 0
    folder = tmp_path / 'project'
    main(['init', str(folder), str(survey)])
    assert main(['import', str(folder), str(responses)]) == 0
    assert len(Project(folder).responses()) == 2
