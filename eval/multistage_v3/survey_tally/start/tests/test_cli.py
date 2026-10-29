import csv
import json

import pytest

from surveytally.cli.main import main
from surveytally.files.store import Project

from conftest import POLL


@pytest.fixture
def project(tmp_path, write_file):
    survey = write_file('poll.json', json.dumps(POLL))
    folder = tmp_path / 'project'
    assert main(['init', str(folder), str(survey)]) == 0
    return folder


def test_import_keeps_valid_responses_and_reports_the_rest(project, write_file, capsys):
    path = write_file('responses.csv', (
        'respondent,submitted,region,contact\n'
        'R1,2026-03-01,north,email\n'
        'R2,2026-03-01,mars,email\n'
        'R3,2026-03-02,south,phone\n'
    ))
    assert main(['import', str(project), str(path)]) == 3
    out = capsys.readouterr().out
    assert 'read 3 responses: 2 valid, 1 rejected' in out
    assert 'R2: region: unknown option mars' in out
    assert [response.respondent for response in Project(project).responses()] == ['R1', 'R3']


def test_a_later_import_replaces_earlier_answers(project, write_file):
    first = write_file('first.csv', 'respondent,submitted,region\nR1,2026-03-01,north\n')
    second = write_file('second.csv', 'respondent,submitted,region\nR1,2026-03-04,east\n')
    main(['import', str(project), str(first)])
    assert main(['import', str(project), str(second)]) == 0
    assert [response.answers for response in Project(project).responses()] == [{'region': 'east'}]


def test_file_errors_exit_with_1(project, write_file, capsys):
    path = write_file('responses.csv', 'respondent,colour\nR1,red\n')
    assert main(['import', str(project), str(path)]) == 1
    assert 'error: row 1: unknown question column colour' in capsys.readouterr().err


def test_export_writes_csv_by_default(project, write_file, tmp_path):
    path = write_file('responses.csv', 'respondent,region\nR1,north\nR2,north\nR3,south\n')
    main(['import', str(project), str(path)])
    out = tmp_path / 'tables.csv'
    assert main(['export', str(project), str(out)]) == 0
    with out.open(newline='', encoding='utf-8') as handle:
        rows = list(csv.reader(handle))
    assert ['region', 'north', '2', '66.7'] in rows


def test_settings_change_the_default_decimals(project, write_file, tmp_path):
    (project / 'surveytally.ini').write_text('[surveytally]\ndecimals = 0\n', encoding='utf-8')
    path = write_file('responses.csv', 'respondent,region\nR1,north\nR2,north\nR3,south\n')
    main(['import', str(project), str(path)])
    out = tmp_path / 'tables.csv'
    main(['export', str(project), str(out)])
    assert 'region,north,2,67' in out.read_text(encoding='utf-8').splitlines()


def test_where_narrows_the_responses(project, write_file, capsys):
    path = write_file('responses.csv', 'respondent,region,contact\nR1,north,email\nR2,south,phone\nR3,north,phone\n')
    main(['import', str(project), str(path)])
    capsys.readouterr()
    assert main(['tally', str(project), '--question', 'contact', '--where', 'region=north']) == 0
    assert 'Base: 2 answered' in capsys.readouterr().out


def test_validate_does_not_need_a_project(write_file, capsys):
    survey = write_file('poll.json', json.dumps(POLL))
    path = write_file('responses.csv', 'respondent,region\nR1,north\n')
    assert main(['validate', str(survey), str(path)]) == 0
    assert '1 of 1 responses are valid' in capsys.readouterr().out
