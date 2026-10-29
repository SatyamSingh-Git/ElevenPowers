"""Survey files, response imports, validation, response exports and the project folder."""
import json

from surveytally.cli.main import main
from surveytally.files.csv_responses import read_responses
from surveytally.files.store import Project
from surveytally.files.survey_file import load_survey
from surveytally.model.responses import Response
from surveytally.reports.responses_export import write_responses
from surveytally.services.validation import validate

SURVEY = {
    'id': 'members',
    'title': 'Members survey',
    'questions': [
        {'id': 'plan', 'type': 'single', 'text': 'Which plan are you on?',
         'options': [{'code': 'basic', 'label': 'Basic'}, {'code': 'plus', 'label': 'Plus'},
                     {'code': 'family', 'label': 'Family'}]},
        {'id': 'features', 'type': 'multi', 'text': 'Which features do you use?',
         'options': ['booking', 'classes', 'sauna', 'pool']},
        {'id': 'value', 'type': 'scale', 'text': 'Value for money', 'low': 1, 'high': 5},
        {'id': 'likely', 'type': 'scale', 'text': 'Would you recommend us?', 'preset': 'likely11'},
        {'id': 'notes', 'type': 'text', 'text': 'Anything else?'},
    ],
}


def write(path, text):
    path.write_text(text, encoding='utf-8')
    return path


def survey_file(tmp_path):
    return write(tmp_path / 'members.json', json.dumps(SURVEY))


def test_survey_file_loads_every_kind_of_question(tmp_path):
    survey = load_survey(survey_file(tmp_path))
    assert survey.question_ids() == ['plan', 'features', 'value', 'likely', 'notes']
    assert survey.question('plan').label_for('plus') == 'Plus'
    assert (survey.question('value').low, survey.question('value').high) == (1, 5)
    assert (survey.question('likely').low, survey.question('likely').high) == (0, 10)


def test_csv_import_reads_each_kind_of_answer(tmp_path):
    survey = load_survey(survey_file(tmp_path))
    path = write(tmp_path / 'responses.csv', (
        'respondent,submitted,plan,features,value,likely,notes\n'
        'M1,2026-04-01,plus,sauna,4,9,Great pool\n'
        'M2,2026-04-02,basic,,2,NA,\n'
    ))
    first, second = read_responses(survey, path)
    assert first.respondent == 'M1'
    assert first.answers == {'plan': 'plus', 'features': ('sauna',), 'value': 4, 'likely': 9, 'notes': 'Great pool'}
    assert second.answers == {'plan': 'basic', 'value': 2}
    assert second.submitted == '2026-04-02'


def test_validation_reports_unknown_options_and_range(tmp_path):
    survey = load_survey(survey_file(tmp_path))
    responses = [
        Response('M1', {'plan': 'gold'}),
        Response('M2', {'value': 7}),
        Response('M3', {'features': ('pool', 'gym')}),
        Response('M4', {'plan': 'family', 'likely': 0}),
    ]
    valid, issues = validate(survey, responses)
    assert [response.respondent for response in valid] == ['M4']
    assert [issue.message for issue in issues] == [
        'plan: unknown option gold', 'value: 7 is outside 1..5', 'features: unknown option gym']


def test_exported_responses_import_again(tmp_path):
    survey = load_survey(survey_file(tmp_path))
    responses = [
        Response('M1', {'plan': 'family', 'features': ('booking', 'pool'), 'value': 5}, '2026-04-03'),
        Response('M2', {'features': ('classes', 'sauna', 'pool'), 'notes': 'Busy at 6pm'}),
        Response('M3', {'plan': 'basic', 'likely': 3}),
    ]
    path = tmp_path / 'export.csv'
    write_responses(survey, responses, path)
    assert read_responses(survey, path) == responses


def test_cli_import_fills_the_project(tmp_path, capsys):
    folder = tmp_path / 'project'
    assert main(['init', str(folder), str(survey_file(tmp_path))]) == 0
    path = write(tmp_path / 'responses.csv', (
        'respondent,submitted,plan,value\n'
        'M1,2026-04-01,plus,4\n'
        'M2,2026-04-01,basic,9\n'
        'M3,2026-04-02,family,3\n'
    ))
    assert main(['import', str(folder), str(path)]) == 3
    assert 'value: 9 is outside 1..5' in capsys.readouterr().out
    stored = Project(folder).responses()
    assert [(response.respondent, response.answers['plan']) for response in stored] == [('M1', 'plus'), ('M3', 'family')]


def test_cli_import_of_clean_file_exits_0(tmp_path):
    folder = tmp_path / 'project'
    main(['init', str(folder), str(survey_file(tmp_path))])
    path = write(tmp_path / 'responses.csv', 'respondent,plan,likely\nM1,plus,10\nM2,basic,0\n')
    assert main(['import', str(folder), str(path)]) == 0
    assert len(Project(folder).responses()) == 2
