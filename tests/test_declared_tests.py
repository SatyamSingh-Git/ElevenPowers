"""The test command a project already declares in tox, make or CI, reduced to runner and paths.

Fixture text is taken from the held-out projects' own files (2026-11-12).
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from core.config import discover_commands
from core.test_command import declared

SETUP = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_setup.py'


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_tox_pytest_drops_plugin_flags_and_placeholders(tmp_path):
    # cachetools: `--cov` needs pytest-cov, and failed with exit 4 as written.
    write(tmp_path, 'tox.ini', '[testenv]\ndeps =\n    pytest\n    pytest-cov\ncommands =\n'
          '    py.test --basetemp={envtmpdir} --cov=cachetools --cov-branch --cov-report term-missing {posargs}\n\n'
          '[testenv:docs]\ncommands = sphinx-build -W -b html docs build\n')
    assert declared(tmp_path) == ('python -m pytest', 'tox.ini')


def test_tox_pytest_keeps_the_paths_it_names(tmp_path):
    # oauthlib
    (tmp_path / 'tests').mkdir()
    write(tmp_path, 'tox.ini', '[testenv]\ndeps=\n    -rrequirements-test.txt\ncommands=\n    pytest --cov=oauthlib tests/\n')
    assert declared(tmp_path) == ('python -m pytest tests/', 'tox.ini')


def test_tox_unittest_with_envpython(tmp_path):
    # more-itertools
    write(tmp_path, 'tox.ini', '[tox]\nenvlist = py\n\n[testenv]\ncommands = {envpython} -m unittest -v {posargs}\n')
    assert declared(tmp_path) == ('python -m unittest', 'tox.ini')


def test_makefile_test_target_with_discover(tmp_path):
    # pycparser
    write(tmp_path, 'Makefile', 'RUFF ?= ruff\n\ncheck:\n\t$(RUFF) check .\n\ntest:\n\tpython3 -m unittest discover\n')
    assert declared(tmp_path) == ('python -m unittest discover', 'Makefile')


def test_makefile_variable_is_dropped(tmp_path):
    write(tmp_path, 'Makefile', 'test:\n\t# run everything\n\tpython -m unittest -v ${tests}\n')
    assert declared(tmp_path) == ('python -m unittest', 'Makefile')


def test_workflow_block_and_inline_runs(tmp_path):
    # tomli, then iniconfig
    write(tmp_path, '.github/workflows/tests.yaml', 'jobs:\n  test:\n    steps:\n    - name: Test with unittest\n'
          '      run: |\n        python -m unittest\n')
    assert declared(tmp_path) == ('python -m unittest', '.github/workflows/tests.yaml')
    (tmp_path / '.github/workflows/tests.yaml').unlink()
    (tmp_path / 'testing').mkdir()
    write(tmp_path, '.github/workflows/main.yml', 'jobs:\n  t:\n    steps:\n      - run: uv python install ${{ matrix.python }}\n'
          '      - run: uv run --with dist/*.whl --with pytest pytest testing --color=yes\n')
    assert declared(tmp_path) == ('python -m pytest testing', '.github/workflows/main.yml')


def test_tox_is_read_before_make_and_ci(tmp_path):
    write(tmp_path, 'tox.ini', '[testenv]\ncommands = {envpython} -m unittest -v {posargs}\n')
    write(tmp_path, 'Makefile', 'test:\n\tpython -m pytest\n')
    assert declared(tmp_path)[1] == 'tox.ini'


@pytest.mark.parametrize('name, text', [
    ('Makefile', 'test:\n\tcd sub && python -m pytest\n'),
    ('Makefile', 'test:\n\ttox\n'),
    ('Makefile', 'test:\n\tpip install -e . && pytest\n'),
    ('tox.ini', '[testenv]\ncommands = nox -s tests\n'),
    ('.github/workflows/ci.yml', 'jobs:\n  t:\n    steps:\n      - run: pytest\n        working-directory: sub\n'),
    ('tox.ini', '[testenv]\ncommands = pytest "unclosed\n'),
    ('tox.ini', '[testenv]\nchangedir = tests\ncommands = pytest\n'),
    # ElevenPowers' own execution-reliability.yml: the package name is not the runner.
    ('.github/workflows/ci.yml', 'jobs:\n  t:\n    steps:\n      - run: python -m pip install pytest\n'),
    ('Makefile', 'test:\n\tuv pip install pytest pytest-cov\n'),
])
def test_refused_declarations_give_no_command(tmp_path, name, text):
    write(tmp_path, name, text)
    assert declared(tmp_path) is None


def test_a_refused_declaration_stops_the_search(tmp_path):
    # The tests run from `sub`; a weaker source's bare `pytest` would run the wrong ones.
    write(tmp_path, 'Makefile', 'test:\n\tcd sub && python -m pytest\n')
    write(tmp_path, '.github/workflows/ci.yml', 'jobs:\n  t:\n    steps:\n      - run: pytest\n')
    assert declared(tmp_path) is None


def test_an_explicit_command_is_not_credited_to_the_declaration(tmp_path):
    from core.config import declare, load
    write(tmp_path, 'tox.ini', '[testenv]\ncommands = {envpython} -m unittest -v {posargs}\n')
    assert load(tmp_path).origins == {'tests': 'tox.ini'}
    declare(tmp_path, 'tests', 'python -m unittest')
    assert load(tmp_path).origins == {}


def test_oversized_file_is_skipped(tmp_path):
    write(tmp_path, 'tox.ini', '[testenv]\ncommands = pytest\n' + '#' * (256 * 1024))
    assert declared(tmp_path) is None


def test_manifest_discovery_and_explicit_commands_still_win(tmp_path):
    write(tmp_path, 'tox.ini', '[testenv]\ncommands = {envpython} -m unittest -v {posargs}\n')
    assert discover_commands(tmp_path)['tests'] == 'python -m unittest'
    write(tmp_path, 'package.json', json.dumps({'scripts': {'test': 'node t.js'}}))
    assert discover_commands(tmp_path)['tests'] == 'npm run test'


def test_nothing_declared_still_gives_no_command(tmp_path):
    (tmp_path / 'tests').mkdir()
    (tmp_path / 'tests/test_a.py').write_text('def test_a():\n    assert True\n')
    assert declared(tmp_path) is None and 'tests' not in discover_commands(tmp_path)


def test_setup_summary_names_where_the_command_came_from(tmp_path):
    subprocess.run(['git', 'init', '-q'], cwd=tmp_path, check=True)
    write(tmp_path, 'tox.ini', '[testenv]\ncommands = {envpython} -m unittest -v {posargs}\n')
    done = subprocess.run([sys.executable, str(SETUP), 'codex', '--project', str(tmp_path)],
                          capture_output=True, text=True, encoding='utf-8')
    assert 'tests: python -m unittest (from tox.ini)' in done.stdout
    assert 'No test command found' not in done.stdout
