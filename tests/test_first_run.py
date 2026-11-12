"""What `ep_setup` tells a person on a project it has never seen."""
import json
from pathlib import Path
import subprocess
import sys

SOURCE = Path(__file__).resolve().parents[1]
SETUP = SOURCE / 'plugin/bin/ep_setup.py'


def setup(project, *extra):
    return subprocess.run([sys.executable, str(SETUP), 'codex', '--project', str(project), *extra],
                          capture_output=True, text=True, encoding='utf-8')


def node_project(root):
    subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
    (root / 'package.json').write_text(json.dumps({'scripts': {'test': 'node t.js', 'lint': 'eslint .'}}))
    (root / '.cursor/rules').mkdir(parents=True)
    (root / '.cursor/rules/a.mdc').write_text('---\nglobs: src/**\n---\nKeep handlers pure.\n')
    (root / '.github/instructions').mkdir(parents=True)
    (root / '.github/instructions/ts.instructions.md').write_text('---\napplyTo: "**/*.ts"\n---\nUse strict types.\n')
    return root


def test_summary_says_what_it_found_and_what_to_do_next(tmp_path):
    done = setup(node_project(tmp_path))
    assert done.returncode == 0, done.stderr
    text = done.stdout
    assert 'ElevenPowers is set up for Codex' in text
    assert 'tests: npm run test' in text and 'lint: npm run lint' in text
    assert '1 Cursor' in text and '1 Copilot' in text
    assert 'Next: start a new Codex session in this project' in text
    assert 'ep_ready.py codex' in text
    assert 'Needs attention' not in text
    assert 'Stage ' not in text and len(text.splitlines()) <= 16
    assert text.isascii()


def test_no_test_command_is_named_with_the_line_that_declares_one(tmp_path):
    subprocess.run(['git', 'init', '-q'], cwd=tmp_path, check=True)
    (tmp_path / 'tests').mkdir()
    (tmp_path / 'tests/test_a.py').write_text('def test_a():\n    assert True\n')
    text = setup(tmp_path).stdout
    assert 'Needs attention' in text
    assert 'No test command found' in text
    assert str(tmp_path) in text and 'your test command' in text


def test_suggested_commands_survive_a_path_with_a_space(tmp_path):
    import shlex
    project = tmp_path / 'my project'
    project.mkdir()
    subprocess.run(['git', 'init', '-q'], cwd=project, check=True)
    text = setup(project).stdout
    line = next(l for l in text.splitlines() if '--tests' in l)
    suggested = line.split('declare it: ', 1)[1]
    words = [w.strip('"') for w in shlex.split(suggested, posix=sys.platform != 'win32')]
    assert words[words.index('--project') + 1] == str(project)
    rules = next(l for l in text.splitlines() if 'Declared rules' in l)
    assert '--project' in rules and str(project) in rules


def test_tests_flag_declares_the_command_and_keeps_other_settings(tmp_path):
    subprocess.run(['git', 'init', '-q'], cwd=tmp_path, check=True)
    folder = tmp_path / '.elevenpowers'
    folder.mkdir()
    (folder / 'config.json').write_text(json.dumps({'profile': 'guide', 'commands': {'lint': 'ruff check .'}}))
    done = setup(tmp_path, '--tests', 'python -m pytest -q')
    assert done.returncode == 0, done.stderr
    saved = json.loads((folder / 'config.json').read_text())
    assert saved == {'profile': 'guide', 'commands': {'lint': 'ruff check .', 'tests': 'python -m pytest -q'}}
    assert 'tests: python -m pytest -q' in done.stdout
    assert 'No test command found' not in done.stdout


def test_tests_flag_refuses_an_empty_command_and_an_unreadable_config(tmp_path):
    subprocess.run(['git', 'init', '-q'], cwd=tmp_path, check=True)
    assert setup(tmp_path, '--tests', '  ').returncode != 0
    folder = tmp_path / '.elevenpowers'
    folder.mkdir(exist_ok=True)
    (folder / 'config.json').write_text('{broken')
    done = setup(tmp_path, '--tests', 'python -m pytest')
    assert done.returncode != 0
    assert (folder / 'config.json').read_text() == '{broken'


def test_unreadable_rule_file_is_listed_as_needing_attention(tmp_path):
    node_project(tmp_path)
    (tmp_path / '.cursor/rules/bad.mdc').write_text('---\nglobs: [unclosed\n---\nx\n')
    text = setup(tmp_path).stdout
    assert 'Needs attention' in text
    line = next(l for l in text.splitlines() if '.cursor/rules/bad.mdc' in l)
    assert 'ep_milestones.py' in line and line.rstrip(')').endswith('--scoped')


def test_strict_mode_is_said_out_loud(tmp_path):
    text = setup(node_project(tmp_path)).stdout
    assert 'Mode: strict' in text
    folder = tmp_path / '.elevenpowers'
    (folder / 'config.json').write_text(json.dumps({'profile': 'guide'}))
    assert 'Mode: guide' in setup(tmp_path).stdout
