"""The reviewer's report: would anything notice if this change were undone?"""
import shutil
import subprocess
import sys

import pytest

from core.review import NOT_PINNED, PINNED, UNKNOWN, review

PYTEST = f'"{sys.executable}" -m pytest tests -q -p no:cacheprovider'
GIT = ['git', '-c', 'user.email=e@e', '-c', 'user.name=e', '-c', 'core.autocrlf=false']
MOD = 'def value():\n    return 1\n'
CHANGED = 'def value():\n    return 2\n'
LOOSE = 'from pkg.mod import value\n\n\ndef test_int():\n    assert isinstance(value(), int)\n'
PINNING = 'from pkg.mod import value\n\n\ndef test_two():\n    assert value() == 2\n'


def _git(root, *args):
    return subprocess.run([*GIT, *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def _commit(root, files, deleted=()):
    for rel, body in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(body, encoding='utf-8', newline='\n')
    for rel in deleted:
        (root / rel).unlink()
    _git(root, 'add', '-A')
    _git(root, 'commit', '-qm', 'step')
    return _git(root, 'rev-parse', 'HEAD')


def _project(tmp_path, files=None):
    root = tmp_path / 'project'
    root.mkdir(parents=True)
    _git(root, 'init', '-q')
    base = _commit(root, files or {'pkg/__init__.py': '', 'pkg/mod.py': MOD, 'tests/test_mod.py': LOOSE})
    return root, base


def test_a_change_its_test_pins_is_pinned_by_that_test(tmp_path):
    root, base = _project(tmp_path)
    _commit(root, {'pkg/mod.py': CHANGED, 'tests/test_two.py': PINNING})
    report = review(root, base, command=PYTEST)
    assert report['verdict'] == PINNED
    assert report['pinning'] == ['tests/test_two.py::test_two']
    assert report['undone'] == ['pkg/mod.py']


def test_a_change_no_test_notices_is_not_pinned(tmp_path):
    root, base = _project(tmp_path)
    _commit(root, {'pkg/mod.py': CHANGED})
    report = review(root, base, command=PYTEST)
    assert report['verdict'] == NOT_PINNED
    assert report['pinning'] == []


def test_a_test_already_red_at_head_is_not_counted_as_pinning(tmp_path):
    root, base = _project(tmp_path, {'pkg/__init__.py': '', 'pkg/mod.py': MOD, 'tests/test_mod.py': LOOSE,
                                     'tests/test_broken.py': 'def test_broken():\n    assert False\n'})
    _commit(root, {'pkg/mod.py': CHANGED})
    report = review(root, base, command=PYTEST)
    assert report['verdict'] == NOT_PINNED
    assert report['runs'][0]['failing'] == ['tests/test_broken.py::test_broken']


def test_a_pinned_change_beside_a_red_test_names_only_the_new_failure(tmp_path):
    root, base = _project(tmp_path, {'pkg/__init__.py': '', 'pkg/mod.py': MOD, 'tests/test_mod.py': LOOSE,
                                     'tests/test_broken.py': 'def test_broken():\n    assert False\n'})
    _commit(root, {'pkg/mod.py': CHANGED, 'tests/test_two.py': PINNING})
    report = review(root, base, command=PYTEST)
    assert report['verdict'] == PINNED
    assert report['pinning'] == ['tests/test_two.py::test_two']


def test_a_pinning_assertion_added_to_an_existing_test_file_stays_when_the_change_is_undone(tmp_path):
    root, base = _project(tmp_path)
    _commit(root, {'pkg/mod.py': CHANGED, 'tests/test_mod.py': LOOSE + '\n\ndef test_two():\n    assert value() == 2\n'})
    report = review(root, base, command=PYTEST)
    assert report['verdict'] == PINNED
    assert report['pinning'] == ['tests/test_mod.py::test_two']


def test_a_test_that_cannot_import_with_the_change_undone_is_named(tmp_path):
    root, base = _project(tmp_path)
    _commit(root, {'pkg/mod.py': CHANGED + '\n\ndef doubled():\n    return 4\n',
                   'tests/test_doubled.py': 'from pkg.mod import doubled\n\n\ndef test_doubled():\n    assert doubled() == 4\n'})
    report = review(root, base, command=PYTEST)
    assert report['verdict'] == PINNED
    assert report['pinning'] == ['tests/test_doubled.py']


def test_a_path_that_reads_as_a_glob_puts_back_only_itself(tmp_path):
    # Read as a pattern, git expands lib[.]spec.py to the test lib.spec.py beside it too,
    # and the test being judged is undone with the change (watched with git 2.45).
    check = 'import runpy\nvalue = runpy.run_path("lib[.]spec.py")["VALUE"]\nraise SystemExit(0 if {} else 1)\n'
    root, base = _project(tmp_path, {'lib[.]spec.py': 'VALUE = 1\n', 'lib.spec.py': check.format('value >= 1')})
    _commit(root, {'lib[.]spec.py': 'VALUE = 2\n', 'lib.spec.py': check.format('value == 2')})
    report = review(root, base, command=f'"{sys.executable}" lib.spec.py')
    assert report['undone'] == ['lib[.]spec.py']
    assert report['verdict'] == PINNED


def test_a_removal_its_test_pins_is_pinned(tmp_path):
    files = {'pkg/__init__.py': '', 'pkg/mod.py': MOD, 'pkg/legacy.py': 'OLD = 1\n', 'tests/test_mod.py': LOOSE}
    root, base = _project(tmp_path, files)
    gone = ('import importlib.util\n\n\ndef test_legacy_is_gone():\n'
            '    assert importlib.util.find_spec("pkg.legacy") is None\n')
    _commit(root, {'tests/test_gone.py': gone}, deleted=['pkg/legacy.py'])
    report = review(root, base, command=PYTEST)
    assert report['verdict'] == PINNED
    assert report['undone'] == ['pkg/legacy.py']


def test_files_the_change_added_are_kept_so_an_added_only_change_is_unknown(tmp_path):
    root, base = _project(tmp_path)
    _commit(root, {'pkg/new.py': 'def twice(x):\n    return 2 * x\n',
                   'tests/test_new.py': 'from pkg.new import twice\n\n\ndef test_twice():\n    assert twice(2) == 4\n'})
    report = review(root, base, command=PYTEST)
    assert report['verdict'] == UNKNOWN
    assert report['kept'] == ['pkg/new.py']
    assert 'added' in report['reason']


def test_a_change_to_tests_alone_is_unknown(tmp_path):
    root, base = _project(tmp_path)
    _commit(root, {'tests/test_two.py': PINNING})
    report = review(root, base, command=PYTEST)
    assert report['verdict'] == UNKNOWN
    assert report['reason'] == 'the change touched only tests'
    assert report['runs'] == []


def test_a_suite_that_changes_its_mind_on_the_same_tree_is_unknown(tmp_path):
    root, base = _project(tmp_path)
    marker = tmp_path / 'ran-once'
    flaky = (f'from pathlib import Path\n\n\ndef test_first_run_only():\n'
             f'    marker = Path({str(marker)!r})\n    seen = marker.exists()\n    marker.touch()\n    assert not seen\n')
    _commit(root, {'pkg/mod.py': CHANGED, 'tests/test_flaky.py': flaky})
    report = review(root, base, command=PYTEST)
    assert report['verdict'] == UNKNOWN
    assert 'same tree' in report['reason']


def test_without_a_declared_command_nothing_runs(tmp_path):
    root, base = _project(tmp_path)
    _commit(root, {'pkg/mod.py': CHANGED, 'tests/test_two.py': PINNING})
    report = review(root, base)
    assert report['verdict'] == UNKNOWN
    assert report['runs'] == []


def test_the_declared_command_is_used_when_none_is_given(tmp_path):
    from core.config import Config, save
    root, base = _project(tmp_path)
    _commit(root, {'pkg/mod.py': CHANGED, 'tests/test_two.py': PINNING})
    save(root, Config(commands={'tests': PYTEST}))
    assert review(root, base)['verdict'] == PINNED


def test_a_run_that_times_out_is_unknown(tmp_path):
    root, base = _project(tmp_path)
    slow = 'import time\n\n\ndef test_slow():\n    time.sleep(30)\n'
    _commit(root, {'pkg/mod.py': CHANGED, 'tests/test_slow.py': slow})
    report = review(root, base, command=PYTEST, timeout=3)
    assert report['verdict'] == UNKNOWN
    assert 'timed out' in report['reason']
    assert len(report['runs']) == 1


def test_an_unknown_ref_is_an_error_not_a_verdict(tmp_path):
    root, _ = _project(tmp_path)
    with pytest.raises(ValueError):
        review(root, 'no-such-ref', command=PYTEST)


def test_runs_write_no_bytecode(tmp_path):
    # An undone file the same size as the change, restored within a second, keeps the
    # change's .pyc and silently runs it; eval/heldout_vacuity measured 3 of 6 runs.
    from core.review import _run
    check = f'"{sys.executable}" -c "import sys; sys.exit(0 if sys.dont_write_bytecode else 1)"'
    assert _run('head', check, tmp_path, 60)['exit'] == 0


def test_a_runner_that_names_no_test_is_judged_by_its_exit_code(tmp_path):
    files = {'mod.py': MOD, 'check.py': 'from mod import value\nraise SystemExit(0 if value() >= 1 else 1)\n'}
    root, base = _project(tmp_path, files)
    _commit(root, {'mod.py': CHANGED, 'check.py': 'from mod import value\nraise SystemExit(0 if value() == 2 else 1)\n'})
    report = review(root, base, command=f'"{sys.executable}" check.py')
    # check.py is not a test file by name, so it is put back too and nothing can notice.
    assert report['verdict'] == NOT_PINNED
    files['tests/check_two.py'] = 'import sys\nsys.path.insert(0, ".")\nfrom mod import value\nraise SystemExit(0 if value() == 2 else 1)\n'
    root, base = _project(tmp_path / 'named', files)
    _commit(root, {'mod.py': CHANGED})
    report = review(root, base, command=f'"{sys.executable}" tests/check_two.py')
    assert report['verdict'] == PINNED
    assert report['pinning'] == []
    assert report['named'] is False


@pytest.mark.skipif(shutil.which('node') is None, reason='node is optional')
def test_an_unrelated_runner_is_read_both_ways(tmp_path):
    test = ('const test = require("node:test");\nconst assert = require("node:assert");\n'
            'const {value} = require("../lib/mod.js");\n')
    files = {'lib/mod.js': 'exports.value = () => 1;\n',
             'test/mod.test.js': test + 'test("number", () => assert.strictEqual(typeof value(), "number"));\n'}
    root, base = _project(tmp_path, files)
    _commit(root, {'lib/mod.js': 'exports.value = () => 2;\n'})
    assert review(root, base, command='node --test')['verdict'] == NOT_PINNED
    _commit(root, {'test/two.test.js': test + 'test("two", () => assert.strictEqual(value(), 2));\n'})
    assert review(root, base, command='node --test')['verdict'] == PINNED


@pytest.mark.skipif(shutil.which('node') is None, reason='node is optional')
def test_installed_js_dependencies_are_available_to_the_runs(tmp_path):
    test = ('const test = require("node:test");\nconst assert = require("node:assert");\n'
            'const {value} = require("../lib/mod.js");\nconst dep = require("dep");\n')
    files = {'.gitignore': 'node_modules/\n', 'lib/mod.js': 'exports.value = () => 1;\n',
             'test/mod.test.js': test + 'test("number", () => assert.strictEqual(typeof value(), dep.kind));\n'}
    root, base = _project(tmp_path, files)
    (root / 'node_modules' / 'dep').mkdir(parents=True)
    (root / 'node_modules' / 'dep' / 'index.js').write_text('exports.kind = "number";\n', encoding='utf-8')
    _commit(root, {'lib/mod.js': 'exports.value = () => 2;\n',
                   'test/two.test.js': test + 'test("two", () => assert.strictEqual(value(), 2));\n'})
    assert review(root, base, command='node --test')['verdict'] == PINNED


def test_the_reviewers_checkout_is_left_exactly_as_it_was(tmp_path):
    root, base = _project(tmp_path)
    head = _commit(root, {'pkg/mod.py': CHANGED, 'tests/test_two.py': PINNING})
    (root / 'scratch.txt').write_text('uncommitted\n', encoding='utf-8')
    review(root, base, command=PYTEST)
    assert _git(root, 'rev-parse', 'HEAD') == head
    assert _git(root, 'status', '--porcelain') == '?? scratch.txt'
    assert (root / 'pkg' / 'mod.py').read_text(encoding='utf-8') == CHANGED
    assert len(_git(root, 'worktree', 'list').splitlines()) == 1


def test_head_can_be_a_commit_other_than_the_checkout(tmp_path):
    root, base = _project(tmp_path)
    head = _commit(root, {'pkg/mod.py': CHANGED, 'tests/test_two.py': PINNING})
    _commit(root, {'tests/test_two.py': 'def test_nothing():\n    pass\n'})
    report = review(root, base, head, command=PYTEST)
    assert report['verdict'] == PINNED
    assert report['head']['commit'] == head
