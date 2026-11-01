"""The reviewer's report: would anything notice if this change were undone?"""
import shutil
import subprocess
import sys

import pytest

from core.review import NOT_PINNED, PINNED, UNKNOWN, review

PYTEST = f'"{sys.executable}" -m pytest tests -q -p no:cacheprovider'
cosmic = pytest.mark.skipif(__import__('importlib').util.find_spec('cosmic_ray') is None,
                            reason='optional Cosmic Ray is not installed')
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


def test_a_test_whose_setup_errors_is_named_once(tmp_path):
    # pytest prints `ERROR tests/test_fix.py::test_uses - ...`; the collection-error
    # pattern alone would also name the bare file.
    root, base = _project(tmp_path)
    fixture = ('import pytest\nfrom pkg.mod import value\n\n\n@pytest.fixture\ndef two():\n'
               '    assert value() == 2\n    return value()\n\n\ndef test_uses(two):\n    assert two == 2\n')
    _commit(root, {'pkg/mod.py': CHANGED, 'tests/test_fix.py': fixture})
    report = review(root, base, command=PYTEST)
    assert report['pinning'] == ['tests/test_fix.py::test_uses']


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


def test_an_interrupted_review_leaves_no_worktree_even_a_locked_one(tmp_path, monkeypatch):
    # An interrupted `worktree add` leaves its worktree locked, which `remove --force` refuses.
    import core.review as module
    root, base = _project(tmp_path)
    _commit(root, {'pkg/mod.py': CHANGED})

    def interrupted(*args, **kwargs):
        subprocess.run(['git', 'worktree', 'lock', str(args[2])], cwd=root, check=True)
        raise KeyboardInterrupt

    monkeypatch.setattr(module, '_run', interrupted)
    with pytest.raises(KeyboardInterrupt):
        review(root, base, command=PYTEST)
    assert len(_git(root, 'worktree', 'list').splitlines()) == 1


@pytest.mark.parametrize('failure', ['timeout', 'output'])
def test_a_git_command_that_hangs_or_floods_is_an_error_not_a_traceback(tmp_path, monkeypatch, failure):
    import core.review as module
    root, base = _project(tmp_path)

    def broken(command, **kwargs):
        if failure == 'timeout':
            raise subprocess.TimeoutExpired(command, 1)
        raise module.process.OutputLimitExceeded('too much')

    monkeypatch.setattr(module.process, 'run', broken)
    with pytest.raises(ValueError, match='git rev-parse'):
        review(root, base, command=PYTEST)


def test_the_projects_git_hooks_do_not_run(tmp_path):
    root, base = _project(tmp_path)
    _commit(root, {'pkg/mod.py': CHANGED, 'tests/test_two.py': PINNING})
    marker = tmp_path / 'hook-ran'
    hook = root / '.git' / 'hooks' / 'post-checkout'
    hook.write_text(f'#!/bin/sh\ntouch "{marker.as_posix()}"\n', encoding='utf-8', newline='\n')
    hook.chmod(0o755)
    subprocess.run(['git', 'checkout', '-q', 'HEAD~1'], cwd=root, check=True)
    assert marker.exists()  # the hook does run for an ordinary checkout here
    marker.unlink()
    subprocess.run(['git', 'checkout', '-q', '-'], cwd=root, check=True)
    marker.unlink()
    assert review(root, base, command=PYTEST)['verdict'] == PINNED
    assert not marker.exists()


def test_a_project_in_a_subfolder_runs_from_that_folder(tmp_path):
    files = {'app/pkg/__init__.py': '', 'app/pkg/mod.py': MOD, 'app/tests/test_mod.py': LOOSE, 'README.md': 'x\n'}
    root, base = _project(tmp_path, files)
    _commit(root, {'app/pkg/mod.py': CHANGED, 'app/tests/test_two.py': PINNING})
    report = review(root / 'app', base, command=PYTEST)
    assert report['verdict'] == PINNED
    assert report['pinning'] == ['tests/test_two.py::test_two']


@cosmic
def test_mutation_in_a_subfolder_project_says_why_it_cannot_attribute_lines(tmp_path):
    files = {'app/pkg/__init__.py': '', 'app/pkg/mod.py': MOD, 'app/tests/test_mod.py': LOOSE}
    root, base = _project(tmp_path, files)
    _commit(root, {'app/pkg/mod.py': CHANGED, 'app/tests/test_two.py': PINNING})
    strength = review(root / 'app', base, command=PYTEST, strength=True)['strength']
    assert any('repository root' in issue for issue in strength['issues'])


@pytest.mark.skipif(shutil.which('node') is None, reason='node is optional')
def test_a_tracked_node_modules_is_used_as_checked_out(tmp_path):
    test = ('const test = require("node:test");\nconst assert = require("node:assert");\n'
            'const {value} = require("../lib/mod.js");\nconst dep = require("dep");\n')
    files = {'node_modules/dep/index.js': 'exports.kind = "number";\n', 'lib/mod.js': 'exports.value = () => 1;\n',
             'test/mod.test.js': test + 'test("number", () => assert.strictEqual(typeof value(), dep.kind));\n'}
    root, base = _project(tmp_path, files)
    _commit(root, {'lib/mod.js': 'exports.value = () => 2;\n',
                   'test/two.test.js': test + 'test("two", () => assert.strictEqual(value(), 2));\n'})
    assert review(root, base, command='node --test')['verdict'] == PINNED


def test_head_can_be_a_commit_other_than_the_checkout(tmp_path):
    root, base = _project(tmp_path)
    head = _commit(root, {'pkg/mod.py': CHANGED, 'tests/test_two.py': PINNING})
    _commit(root, {'tests/test_two.py': 'def test_nothing():\n    pass\n'})
    report = review(root, base, head, command=PYTEST)
    assert report['verdict'] == PINNED
    assert report['head']['commit'] == head


def _report(**overrides):
    commit = {'ref': 'x', 'commit': 'a' * 40, 'tree': 'b' * 40}
    report = {'schema': 1, 'base': commit, 'head': {**commit, 'commit': 'c' * 40}, 'command': 'npm test',
              'verdict': PINNED, 'reason': '1 test fails with the change undone and passes with it',
              'pinning': ['tests/test_two.py::test_two'], 'named': True, 'runs': [], 'tests': ['tests/test_two.py'],
              'undone': ['pkg/mod.py'], 'kept': [], 'unknown': ['A limit.'], 'strength': None}
    return {**report, **overrides}


POSITIVE = 'def positive(value):\n    return value > 0\n'
WEAK = 'from pkg.mod import positive\n\n\ndef test_two():\n    assert positive(2)\n'
STRONG = WEAK + ('\n\ndef test_edges():\n    assert positive(1)\n    assert not positive(0)\n'
                 '    assert not positive(-1)\n')


def _strength_project(tmp_path, tests):
    root, base = _project(tmp_path, {'pkg/__init__.py': '', 'pkg/mod.py': 'def positive(value):\n    return True\n',
                                     'tests/test_mod.py': 'def test_nothing():\n    pass\n'})
    _commit(root, {'pkg/mod.py': POSITIVE, 'tests/test_mod.py': tests})
    return root, base


@cosmic
def test_a_changed_line_a_weak_test_misses_is_named(tmp_path):
    root, base = _strength_project(tmp_path, WEAK)
    strength = review(root, base, command=PYTEST, strength=True)['strength']
    assert {(line['path'], line['line'], line['context']) for line in strength['unpinned']} == {('pkg/mod.py', 2, 'positive')}
    assert 'ReplaceComparisonOperator_Gt_GtE' in strength['unpinned'][0]['operators']


@cosmic
def test_changed_lines_strong_tests_cover_are_not_named(tmp_path):
    root, base = _strength_project(tmp_path, STRONG)
    strength = review(root, base, command=PYTEST, strength=True)['strength']
    assert strength['unpinned'] == []
    assert strength['summary']['detected'] > 0


@cosmic
def test_mutation_follows_the_projects_own_strength_settings(tmp_path):
    from core.config import Config, save
    root, base = _strength_project(tmp_path, WEAK)
    save(root, Config(strength={'max_mutants': 2}))
    assert review(root, base, command=PYTEST, strength=True)['strength']['attempts'] == 2


@cosmic
def test_a_change_that_only_adds_files_still_has_its_lines_measured(tmp_path):
    root, base = _project(tmp_path)
    _commit(root, {'pkg/sign.py': POSITIVE.replace('pkg.mod', 'pkg.sign'),
                   'tests/test_sign.py': WEAK.replace('pkg.mod', 'pkg.sign')})
    report = review(root, base, command=PYTEST, strength=True)
    assert report['verdict'] == UNKNOWN
    assert report['reason'] == 'the change only added files, which are kept when it is undone'
    assert report['runs'] == []
    assert {line['path'] for line in report['strength']['unpinned']} == {'pkg/sign.py'}


def test_mutation_runs_only_when_asked(tmp_path):
    root, base = _project(tmp_path)
    _commit(root, {'pkg/mod.py': CHANGED})
    assert review(root, base, command=PYTEST)['strength'] is None


def test_unpinned_lines_are_listed_with_what_went_unnoticed():
    from core.review import markdown
    lines = [{'path': 'pkg/mod.py', 'line': n, 'end_line': n, 'context': 'positive', 'operators': ['NumberReplacer', 'X']}
             for n in range(1, 13)]
    strength = {'state': 'complete', 'issues': ['an engine issue'], 'attempts': 30, 'unpinned': lines,
                'summary': {'detected': 6, 'undetected': 24, 'incomplete': 0}}
    text = markdown(_report(strength=strength, unknown=['A limit.', 'Mutation analysis: an engine issue']))
    assert '24 of 30 changes tried on the changed lines went unnoticed' in text
    assert r'- pkg/mod\.py:1 in positive: NumberReplacer, X' in text
    assert '- and 2 more lines; the JSON report lists them all' in text
    assert r'pkg/mod\.py:10 in' in text and r'pkg/mod\.py:11 in' not in text
    assert r'- Mutation analysis: an engine issue' in text
    shown = {**strength, 'unpinned': [{**lines[0], 'context': ''}] * 10}
    text = markdown(_report(strength=shown))
    assert 'more lines' not in text
    assert r'- pkg/mod\.py:1 in module: NumberReplacer, X' in text


@cosmic
def test_the_command_mutates_only_when_asked(tmp_path):
    root, base = _strength_project(tmp_path, WEAK)
    cli = [sys.executable, 'plugin/bin/ep_review.py', '--project', str(root), '--base', base, '--command', PYTEST]
    assert r'- pkg/mod\.py:2 in positive' in subprocess.run([*cli, '--strength'], capture_output=True, text=True).stdout
    assert 'Run again with --strength' in subprocess.run(cli, capture_output=True, text=True).stdout


def test_changed_lines_every_test_noticed_say_so():
    from core.review import markdown
    strength = {'state': 'complete', 'issues': [], 'attempts': 5, 'unpinned': [],
                'summary': {'detected': 5, 'undetected': 0, 'incomplete': 0}}
    assert 'All 5 changes tried on the changed lines were noticed by a test.' in markdown(_report(strength=strength))
    assert 'old' not in markdown(_report(strength=strength)).split('## What was run')[0].split('## Lines')[1]


def test_lines_noticed_by_tests_that_cannot_tell_old_from_new_say_both():
    # Seen on a real v3 stage: every mutant was killed, yet undoing the change was not noticed.
    from core.review import markdown
    strength = {'state': 'complete', 'issues': [], 'attempts': 6, 'unpinned': [],
                'summary': {'detected': 6, 'undetected': 0, 'incomplete': 0}}
    text = markdown(_report(verdict=NOT_PINNED, pinning=[], strength=strength))
    assert ('All 6 changes tried on the changed lines were noticed by a test. The tests run these lines, '
            'but none of them tells the new behaviour from the old.') in text


def test_mutation_that_could_not_run_says_so_and_how_to_ask_for_it():
    from core.review import markdown
    strength = {'state': 'unavailable', 'issues': ['optional Cosmic Ray 8.7.0 is not installed'], 'attempts': 0,
                'unpinned': [], 'summary': {'detected': 0, 'undetected': 0, 'incomplete': 0}}
    assert 'Not measured: unavailable.' in markdown(_report(strength=strength))
    assert 'Not measured. Run again with --strength' in markdown(_report())


def test_mutation_issues_and_its_limit_join_the_unknowns(tmp_path):
    from core.review import _limits
    strength = {'state': 'incomplete', 'issues': ['attempt limit'], 'attempts': 8, 'unpinned': [],
                'summary': {'detected': 8, 'undetected': 0, 'incomplete': 0}}
    limits = _limits(_report(strength=strength, command='npm test'))
    assert 'Mutation analysis: attempt limit' in limits
    assert any('equivalent' in limit for limit in limits)
    assert not any('equivalent' in limit for limit in _limits(_report(command='npm test')))


def test_the_verdict_and_the_tests_that_pin_it_come_first():
    from core.review import markdown
    lines = markdown(_report()).splitlines()
    assert lines[2] == '**PINNED.** 1 test fails with the change undone and passes with it.'
    assert lines[4] == r'- tests/test\_two\.py::test\_two'
    assert lines[5] == ''


def test_a_long_list_of_pinning_tests_is_cut_to_what_can_be_read_in_a_minute():
    from core.review import markdown
    lines = markdown(_report(pinning=[f't{n}' for n in range(12)])).splitlines()
    assert lines[4:15] == [f'- t{n}' for n in range(10)] + ['- and 2 more; the JSON report lists them all']
    assert markdown(_report(pinning=[f't{n}' for n in range(10)])).splitlines()[13:15] == ['- t9', '']


def test_the_reason_reads_as_a_sentence():
    from core.review import markdown
    assert '**NOT PINNED.** No test fails.' in markdown(_report(verdict=NOT_PINNED, pinning=[], reason='no test fails'))


def test_a_change_nothing_notices_tells_the_reviewer_what_to_ask_for():
    from core.review import markdown
    text = markdown(_report(verdict=NOT_PINNED, pinning=[], reason='no test fails'))
    assert '**NOT PINNED.**' in text
    assert 'Ask for a test that fails without this change' in text


def test_a_pin_without_names_says_the_names_are_unknown():
    from core.review import markdown
    assert 'named no test' in markdown(_report(pinning=[], named=False))


def test_every_run_is_listed_with_its_tree_and_every_limit_is_kept():
    from core.review import markdown
    runs = [{'name': name, 'command': 'npm test', 'exit': code, 'seconds': 1.5, 'failing': failing, 'named': True,
             'problem': ''} for name, code, failing in (('head', 0, []), ('undone', 1, ['t']), ('head again', 0, []))]
    text = markdown(_report(runs=runs, unknown=['First limit.', 'Second limit.']))
    assert '| head | ' + 'c' * 12 in text
    assert '| undone | ' + 'c' * 12 + ' with 1 file(s) put back to ' + 'a' * 12 in text
    assert text.count('| npm test |') == 3
    assert '| npm test | 1 | 1 | 1.5 |' in text
    assert r'- First limit\.' in text and r'- Second limit\.' in text
    assert ('Change ' + 'a' * 12 + '..' + 'c' * 12 + ': 1 file(s) put back to base when undone, '
            '0 added and kept, 1 test file(s) changed.') in text


def test_a_run_that_could_not_finish_shows_why_in_place_of_its_exit_code():
    from core.review import markdown
    run = {'name': 'head', 'command': 'npm test', 'exit': None, 'seconds': 3.0, 'failing': [], 'named': False,
           'problem': 'timed out after 3 seconds'}
    assert '| npm test | timed out after 3 seconds | 0 |' in markdown(_report(verdict=UNKNOWN, runs=[run]))


def test_a_report_with_no_runs_says_nothing_was_run():
    from core.review import markdown
    assert 'Nothing was run.' in markdown(_report(verdict=UNKNOWN, runs=[]))


def test_the_command_prints_a_report_and_exits_zero_whatever_the_verdict(tmp_path):
    import json
    root, base = _project(tmp_path)
    _commit(root, {'pkg/mod.py': CHANGED})
    cli = [sys.executable, 'plugin/bin/ep_review.py', '--project', str(root), '--base', base, '--command', PYTEST]
    done = subprocess.run(cli, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert '**NOT PINNED.**' in done.stdout
    assert str(root) not in done.stdout
    done = subprocess.run([*cli, '--format', 'json'], capture_output=True, text=True)
    assert json.loads(done.stdout)['verdict'] == NOT_PINNED
    saved = tmp_path / 'review.md'
    done = subprocess.run([*cli, '--output', str(saved)], capture_output=True, text=True)
    assert done.returncode == 0 and '**NOT PINNED.**' in saved.read_text(encoding='utf-8')


def test_the_command_keeps_the_project_path_out_of_what_it_prints(tmp_path):
    import json
    root, base = _project(tmp_path)
    _commit(root, {'pkg/mod.py': CHANGED})
    command = f'"{sys.executable}" -m pytest "{root / "tests"}" -q -p no:cacheprovider'
    done = subprocess.run([sys.executable, 'plugin/bin/ep_review.py', '--project', str(root), '--base', base,
                           '--command', command, '--format', 'json'], capture_output=True, text=True)
    printed = json.loads(done.stdout)['command']
    assert str(root) not in printed and '<project>' in printed


def test_the_command_passes_its_timeout_to_every_run(tmp_path):
    root, base = _project(tmp_path)
    _commit(root, {'pkg/mod.py': CHANGED, 'tests/test_slow.py': 'import time\n\n\ndef test_slow():\n    time.sleep(30)\n'})
    done = subprocess.run([sys.executable, 'plugin/bin/ep_review.py', '--project', str(root), '--base', base,
                           '--command', PYTEST, '--timeout', '3'], capture_output=True, text=True)
    assert 'timed out after 3' in done.stdout


def test_the_command_exits_two_when_no_report_can_be_made(tmp_path):
    root, _ = _project(tmp_path)
    done = subprocess.run([sys.executable, 'plugin/bin/ep_review.py', '--project', str(root), '--base', 'no-such-ref'],
                          capture_output=True, text=True)
    assert done.returncode == 2
    assert 'no-such-ref' in done.stderr
