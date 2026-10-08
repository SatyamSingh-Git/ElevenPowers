"""Independent contracts; no host, model or native acceptance is simulated."""
import importlib.util

import pytest


def api():
    assert importlib.util.find_spec('eval.preservation_cases'), 'staged preservation cases are missing'
    from eval.preservation_cases import case
    from eval.preservation_oracles import grade
    return case, grade


@pytest.mark.parametrize('name', ['queue', 'inventory'])
def test_gold_fault_and_equivalent_controls(tmp_path, name):
    case, grade = api()
    value = case(name)
    root = tmp_path / name
    root.mkdir()
    for path, content in value['files'].items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
    base = grade(value, 0, root)
    assert base['state'] == 'graded' and base['failed'] == 0 and base['passed'] >= 3
    assert grade(value, 1, root)['failed'] > 0
    for stage in (1, 2):
        (root / 'service.py').write_text(value['gold'][stage - 1], encoding='utf-8')
        good = grade(value, stage, root)
        assert good['state'] == 'graded' and good['failed'] == 0, good
        assert all(row['state'] == 'passed' for row in good['checks'])
        (root / 'service.py').write_text(value['fault'][stage - 1], encoding='utf-8')
        bad = grade(value, stage, root)
        assert bad['state'] == 'graded' and bad['failed'] > 0, bad
        (root / 'service.py').write_text('# equivalent comment\n' + value['gold'][stage - 1], encoding='utf-8')
        assert grade(value, stage, root)['failed'] == 0


def test_import_error_and_missing_source_cannot_count_as_detection(tmp_path):
    case, grade = api()
    value = case('queue')
    assert grade(value, 1, tmp_path)['state'] == 'incomplete'
    (tmp_path / 'service.py').write_text('raise RuntimeError("setup")\n')
    (tmp_path / 'formatting.py').write_text('def render(x): return str(x)\n')
    result = grade(value, 1, tmp_path)
    assert result['state'] == 'incomplete'
    assert result['failed'] == 0


def test_grader_timeout_is_incomplete(tmp_path):
    case, grade = api()
    value = case('queue')
    for name in value['production']:
        (tmp_path / name).write_text('while True: pass\n')
    result = grade(value, 0, tmp_path, seconds=.1)
    assert result['state'] == 'incomplete' and result['failed'] == 0
