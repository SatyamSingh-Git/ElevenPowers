"""A declared rule left behind sends the agent back once, at Stop.

The note before an edit cut lost dependents from 31 of 50 to 15 of 50
(results/rule-groups-acted-on-reviewed). Every one of the 5 that were told and
still lost it ended with the rule changed in one file only, and nothing said so
to the agent: the finding went to the person's end report. The research behind
this (docs/research/audit_2026_11_05) found enforced checks beat advice. Borrowed
from Chromium's IfThisThenThat presubmit, which refuses a change to one side of
a LINT.IfChange pair unless the other changes or the author says why.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CALC_TEST = ("import pathlib, sys\nsys.path.insert(0, str(pathlib.Path(__file__).parents[1] / 'src'))\n"
             "from calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n")
RULE = {'id': 'totals', 'description': 'Totals are summed the same way in calc and report.',
        'inputs': ['src/calc.py', 'src/report.py'],
        'checks': [{'kind': 'test_suite', 'command': 'python -m pytest -q'}]}


def _hook(event, payload):
    return subprocess.run([sys.executable, '-m', 'core.hook', event], input=json.dumps(payload),
                          capture_output=True, text=True, cwd=REPO_ROOT)


def _git(root, *args):
    subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)


def _project(root, config={'rule_gate': True}):
    (root / 'src').mkdir()
    (root / 'tests').mkdir()
    (root / 'src' / 'calc.py').write_text('def add(a, b):\n    return a + b\n', encoding='utf-8')
    (root / 'src' / 'report.py').write_text('def total(rows):\n    return sum(rows)\n', encoding='utf-8')
    (root / 'tests' / 'test_calc.py').write_text(CALC_TEST, encoding='utf-8')
    (root / 'pytest.ini').write_text('[pytest]\n', encoding='utf-8')
    (root / '.gitignore').write_text('__pycache__/\n.pytest_cache/\n.elevenpowers/\n', encoding='utf-8')
    (root / 'elevenpowers.milestones.json').write_text(json.dumps({'schema': 1, 'milestones': [RULE]}),
                                                       encoding='utf-8')
    (root / '.elevenpowers').mkdir()
    (root / '.elevenpowers' / 'config.json').write_text(json.dumps(config), encoding='utf-8')
    _git(root, 'init', '-q')
    _git(root, 'config', 'user.email', 'probe@example.com')
    _git(root, 'config', 'user.name', 'probe')
    _git(root, 'add', '-A')
    _git(root, 'commit', '-q', '-m', 'base')
    _hook('UserPromptSubmit', {'cwd': str(root), 'prompt': 'add a subtract function to src/calc.py'})
    return root


def _edit(root, rel, extra):
    path = root / rel
    body = path.read_text(encoding='utf-8') + extra
    path.write_text(body, encoding='utf-8')
    _hook('PostToolUse', {'cwd': str(root), 'tool_name': 'Write',
                          'tool_input': {'file_path': str(path), 'content': body},
                          'tool_response': {'filePath': str(path)}})


def _tests(root):
    done = subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=root, capture_output=True, text=True)
    _hook('PostToolUse', {'cwd': str(root), 'tool_name': 'Bash', 'tool_input': {'command': 'python -m pytest -q'},
                          'tool_response': {'stdout': done.stdout + done.stderr, 'stderr': '',
                                            'interrupted': False, 'returnCode': done.returncode}})


def _stop(root):
    return _hook('Stop', {'cwd': str(root), 'stop_hook_active': False,
                          'last_assistant_message': 'Added subtract() to src/calc.py; the tests pass.'})


def _decisions(root):
    ledger = json.loads((root / '.elevenpowers' / 'ledger.json').read_text(encoding='utf-8'))
    return [(d['what'], d['why']) for d in ledger['decisions']]


SUBTRACT = '\n\ndef subtract(a, b):\n    return a - b\n'


def test_the_switch_survives_a_saved_config(tmp_path):
    from core.config import Config, load, save
    save(tmp_path, Config(profile='strict', rule_gate=True))
    assert load(tmp_path).rule_gate is True
    save(tmp_path, Config(profile='strict'))
    assert load(tmp_path).rule_gate is False


def test_a_rule_changed_in_one_file_sends_the_agent_back_naming_the_other(tmp_path):
    root = _project(tmp_path)
    _edit(root, 'src/calc.py', SUBTRACT)
    _tests(root)
    done = _stop(root)
    assert done.returncode == 2, (done.stdout, done.stderr)
    assert 'declared rule totals: changed src/calc.py, not src/report.py' in done.stderr, done.stderr
    assert 'or say in your reply why' in done.stderr, done.stderr


def test_it_asks_once_then_lets_the_agent_stop_and_logs_the_release(tmp_path):
    root = _project(tmp_path)
    _edit(root, 'src/calc.py', SUBTRACT)
    _tests(root)
    assert _stop(root).returncode == 2
    done = _stop(root)
    assert done.returncode == 0, done.stderr
    assert 'declared rule totals' in done.stdout, 'the person is still told'
    assert any(what == 'rule gate released' and 'totals' in why for what, why in _decisions(root))


def test_once_the_gate_has_used_its_blocks_a_rule_does_not_add_another(tmp_path):
    root = _project(tmp_path)
    _edit(root, 'src/calc.py', SUBTRACT)
    _tests(root)
    path = root / '.elevenpowers' / 'ledger.json'
    ledger = json.loads(path.read_text(encoding='utf-8'))
    path.write_text(json.dumps({**ledger, 'blocks': 2}), encoding='utf-8')
    done = _stop(root)
    assert done.returncode == 0, done.stderr
    assert 'declared rule totals' in done.stdout
    assert 'UNVERIFIED' not in done.stdout, 'verified work is not reported as unverified for a rule'


def test_the_same_request_sent_again_may_be_asked_again(tmp_path):
    root = _project(tmp_path)
    _edit(root, 'src/calc.py', SUBTRACT)
    _tests(root)
    assert _stop(root).returncode == 2
    _hook('UserPromptSubmit', {'cwd': str(root), 'prompt': 'add a subtract function to src/calc.py'})
    done = _stop(root)
    assert done.returncode == 2 and 'declared rule totals' in done.stderr, (done.stdout, done.stderr)


def test_a_rule_changed_in_every_file_lets_the_agent_stop(tmp_path):
    root = _project(tmp_path)
    _edit(root, 'src/calc.py', SUBTRACT)
    _edit(root, 'src/report.py', '\n\ndef difference(rows):\n    return rows[0] - sum(rows[1:])\n')
    _tests(root)
    done = _stop(root)
    assert done.returncode == 0, done.stderr
    assert 'VERIFIED' in done.stdout and 'declared rule totals' not in done.stdout


def test_a_change_outside_every_rule_lets_the_agent_stop(tmp_path):
    root = _project(tmp_path)
    (root / 'src' / 'names.py').write_text('', encoding='utf-8')
    _git(root, 'add', '-A')
    _git(root, 'commit', '-q', '-m', 'names')
    _edit(root, 'src/names.py', 'def greet(name):\n    return "Hello, " + name\n')
    _tests(root)
    assert _stop(root).returncode == 0


def test_the_guide_profile_reports_the_rule_and_never_blocks(tmp_path):
    root = _project(tmp_path, config={'profile': 'guide', 'rule_gate': True})
    _edit(root, 'src/calc.py', SUBTRACT)
    _tests(root)
    done = _stop(root)
    assert done.returncode == 0, done.stderr
    assert 'declared rule totals: changed src/calc.py, not src/report.py' in done.stdout


def test_by_default_the_rule_stays_a_note_under_strict(tmp_path):
    root = _project(tmp_path, config={})
    _edit(root, 'src/calc.py', SUBTRACT)
    _tests(root)
    done = _stop(root)
    assert done.returncode == 0, done.stderr
    assert 'declared rule totals' in done.stdout


def test_a_failing_change_and_a_rule_left_behind_are_said_in_one_block(tmp_path):
    root = _project(tmp_path)
    _edit(root, 'src/calc.py', '\n\ndef add(a, b):\n    return a - b\n')
    _tests(root)
    done = _stop(root)
    assert done.returncode == 2
    assert 'tests/test_calc.py::test_add' in done.stderr and 'declared rule totals' in done.stderr, done.stderr
    assert json.loads((root / '.elevenpowers' / 'ledger.json').read_text(encoding='utf-8'))['blocks'] == 1
