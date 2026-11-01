"""Seeds for the reviewer study: real changes, the same change untested, and one wrong line."""
import subprocess

from eval.reviewer_seeds import commit_pair, without_tests, wrong


def _tree(root, files):
    for rel, body in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(body, encoding='utf-8')
    return root


def _show(root, ref, rel):
    done = subprocess.run(['git', 'show', f'{ref}:{rel}'], cwd=root, capture_output=True, text=True)
    return done.stdout if done.returncode == 0 else None


def test_a_commit_pair_holds_both_trees_including_deletions(tmp_path):
    before = _tree(tmp_path / 'before', {'src/a.py': 'A = 1\n', 'src/gone.py': 'G = 1\n', 'tests/test_a.py': 't\n'})
    after = _tree(tmp_path / 'after', {'src/a.py': 'A = 2\n', 'src/new.py': 'N = 1\n', 'tests/test_a.py': 't\n'})
    root = tmp_path / 'pair'
    base = commit_pair(before, after, root)
    assert _show(root, base, 'src/a.py') == 'A = 1\n' and _show(root, 'HEAD', 'src/a.py') == 'A = 2\n'
    assert _show(root, base, 'src/gone.py') == 'G = 1\n' and _show(root, 'HEAD', 'src/gone.py') is None
    assert _show(root, base, 'src/new.py') is None and _show(root, 'HEAD', 'src/new.py') == 'N = 1\n'
    assert subprocess.run(['git', 'status', '--porcelain'], cwd=root, capture_output=True, text=True).stdout == ''


def test_a_change_without_its_tests_keeps_its_source_and_the_old_tests(tmp_path):
    before = _tree(tmp_path / 'before', {'src/a.py': 'A = 1\n', 'tests/test_a.py': 'old\n'})
    after = _tree(tmp_path / 'after', {'src/a.py': 'A = 2\n', 'tests/test_a.py': 'new\n', 'tests/test_b.py': 'b\n'})
    out = without_tests(before, after, 'tests', tmp_path / 'out')
    assert (out / 'src' / 'a.py').read_text(encoding='utf-8') == 'A = 2\n'
    assert (out / 'tests' / 'test_a.py').read_text(encoding='utf-8') == 'old\n'
    assert not (out / 'tests' / 'test_b.py').exists()


def test_a_wrong_seed_passes_its_tests_and_breaks_behaviour_that_passed():
    kept = {'s1': 'passed', 's2': 'passed', 'old': 'failed'}
    assert wrong(0, kept, {'s1': 'passed', 's2': 'failed', 'old': 'failed'})
    assert not wrong(1, kept, {'s1': 'passed', 's2': 'failed', 'old': 'failed'})
    assert not wrong(0, kept, dict(kept))
    assert not wrong(0, kept, {'s1': 'passed', 's2': 'passed', 'old': 'timeout'})
    assert wrong(0, kept, {'s1': 'passed', 's2': 'timeout', 'old': 'failed'})
