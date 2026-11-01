"""The reviewer study's sealed runner, driven end to end by a fake reviewer at $0."""
import json
import sys

import pytest

from eval.reviewer_run import collect, command, execute, prepare
from eval.reviewer_seeds import commit_pair

# Answers like a reviewer: names src/m.py:2 when the report is in the prompt, accepts otherwise.
FAKE = '''import json, sys
prompt = sys.stdin.read()
problems = [{"file": "src/m.py", "line": 2, "kind": "wrong_behaviour", "description": "x"}] if "ep_review" in prompt else []
answer = {"decision": "request_changes" if problems else "accept", "problems": problems}
print(json.dumps({"is_error": False, "result": json.dumps(answer), "total_cost_usd": 0.01,
                  "usage": {"output_tokens": 7}, "modelUsage": {"claude-sonnet-5-5": {}}}))
'''


def _tree(root, files):
    for rel, body in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(body, encoding='utf-8', newline='\n')
    return root


def _batch(tmp_path):
    base = {'src/m.py': 'def f(x):\n    return x\n', 'tests/test_m.py': 'def test_ok():\n    assert True\n'}
    before = _tree(tmp_path / 'before', base)
    after = _tree(tmp_path / 'after', {**base, 'src/m.py': 'def f(x):\n    return x + 1\n'})
    seeds = tmp_path / 'seeds'
    manifest = {'seeds': [
        {'seed': 'p-W', 'kind': 'W', 'path': 'src/m.py', 'line': 2, 'end_line': 2, 'request': 'Add one.',
         'command': '"python" -m pytest tests -q -p no:cacheprovider', 'base': commit_pair(before, after, seeds / 'p-W')},
        {'seed': 'p-C', 'kind': 'C', 'request': 'Add one.', 'command': '"python" -m pytest tests -q -p no:cacheprovider',
         'base': commit_pair(before, after, seeds / 'p-C')}]}
    batch = tmp_path / 'batch'
    protocol, gate = prepare(batch, seeds, manifest)
    fake = tmp_path / 'fake.py'
    fake.write_text(FAKE, encoding='utf-8')
    return batch, protocol, gate, [sys.executable, str(fake)]


def test_a_reviewer_call_takes_its_prompt_on_stdin_with_no_tools():
    args = command(['claude.exe'], 'claude-sonnet-5-5')
    assert args[0] == 'claude.exe' and args[1] == '-p' and args[2] == '--model'
    assert args[args.index('--tools') + 1] == ''
    assert '--allowedTools' not in args and 'PROMPT' not in args
    assert 'claudeMdExcludes' in args[args.index('--settings') + 1]


def test_every_slot_runs_once_and_is_graded_by_the_fixed_rules(tmp_path):
    batch, protocol, gate, fake = _batch(tmp_path)
    assert sorted(protocol['slots']) == ['p-C--diff', 'p-C--report', 'p-W--diff', 'p-W--report']
    assert gate['tally']['C']['of'] == 1 and gate['tally']['W']['of'] == 1
    results = {slot: execute(batch, slot, fake) for slot in protocol['slots']}
    assert results['p-W--report']['caught'] is True and results['p-W--diff']['caught'] is False
    assert results['p-C--report']['caught'] is True  # a false alarm on a control
    assert results['p-W--report']['cost'] == 0.01 and results['p-W--report']['state'] == 'graded'
    with pytest.raises(ValueError, match='never retry'):
        execute(batch, 'p-W--diff', fake)
    summary = collect(batch)
    assert summary['analysis']['W']['caught'] == {'diff': 0, 'report': 1}
    assert summary['runs'] == {'scheduled': 4, 'graded': 4, 'other': {}, 'not_launched': 0}


def test_a_changed_input_or_harness_refuses_every_later_call(tmp_path):
    batch, protocol, _, fake = _batch(tmp_path)
    (batch / 'inputs' / 'p-W.md').write_text('tampered', encoding='utf-8')
    with pytest.raises(ValueError, match='frozen input'):
        execute(batch, 'p-W--report', fake)
    protocol['model'] = 'other'
    (batch / 'protocol.json').write_text(json.dumps(protocol), encoding='utf-8')
    with pytest.raises(ValueError, match='sealed protocol'):
        execute(batch, 'p-C--diff', fake)


def test_a_reply_that_is_not_an_answer_is_kept_but_not_scored(tmp_path):
    batch, protocol, _, _ = _batch(tmp_path)
    silent = tmp_path / 'silent.py'
    silent.write_text('import json, sys\nsys.stdin.read()\nprint(json.dumps({"is_error": True, "result": "no"}))\n',
                      encoding='utf-8')
    result = execute(batch, 'p-W--diff', [sys.executable, str(silent)])
    assert result['state'] == 'unreadable' and result['caught'] is None
    assert collect(batch)['runs']['other'] == {'unreadable': 1}


def test_a_batch_is_never_prepared_twice_or_where_an_agent_would_read_a_claude_md(tmp_path):
    batch, _, _, _ = _batch(tmp_path)
    with pytest.raises(ValueError, match='new batch'):
        prepare(batch, tmp_path / 'seeds', {'seeds': []})
    (tmp_path / 'CLAUDE.md').write_text('instructions', encoding='utf-8')
    with pytest.raises(ValueError, match='CLAUDE.md'):
        prepare(tmp_path / 'other', tmp_path / 'seeds', {'seeds': []})


def test_the_harness_the_slot_and_the_diff_are_all_checked_before_a_call(tmp_path, monkeypatch):
    import eval.reviewer_run as module
    batch, _, _, fake = _batch(tmp_path)
    with pytest.raises(ValueError, match='unknown slot'):
        execute(batch, 'p-X--diff', fake)
    (batch / 'inputs' / 'p-C.diff').write_text('tampered', encoding='utf-8')
    with pytest.raises(ValueError, match='frozen input'):
        execute(batch, 'p-C--diff', fake)
    monkeypatch.setattr(module, '_harness', lambda: 'different')
    with pytest.raises(ValueError, match='sealed harness'):
        execute(batch, 'p-W--diff', fake)


def test_a_call_that_prints_nothing_or_runs_out_of_time_is_recorded_as_such(tmp_path, monkeypatch):
    import eval.reviewer_run as module
    batch, _, _, _ = _batch(tmp_path)
    quiet = tmp_path / 'quiet.py'
    quiet.write_text('import sys\nsys.stdin.read()\n', encoding='utf-8')
    assert execute(batch, 'p-W--diff', [sys.executable, str(quiet)])['state'] == 'failed'
    slow = tmp_path / 'slow.py'
    slow.write_text('import sys, time\nsys.stdin.read()\ntime.sleep(20)\n', encoding='utf-8')
    monkeypatch.setattr(module, 'TIMEOUT', 2)
    assert execute(batch, 'p-W--report', [sys.executable, str(slow)])['state'] == 'timed_out'


def test_launching_stops_once_the_subscription_says_its_quota_is_spent(tmp_path):
    from eval.reviewer_run import run
    batch, _, _, _ = _batch(tmp_path)
    spent = tmp_path / 'spent.py'
    spent.write_text('import json, sys\nsys.stdin.read()\n'
                     'print(json.dumps({"is_error": True, "result": "limit", "api_error_status": 429}))\n',
                     encoding='utf-8')
    assert len(run(batch, [sys.executable, str(spent)], workers=1)) == 1
    assert collect(batch)['runs']['not_launched'] == 3


def test_each_seeds_arms_run_together_and_which_goes_first_alternates(tmp_path):
    _, protocol, _, _ = _batch(tmp_path)
    slots = protocol['slots']
    pairs = [slots[i:i + 2] for i in range(0, len(slots), 2)]
    assert all(a.rsplit('--', 1)[0] == b.rsplit('--', 1)[0] for a, b in pairs)
    assert [pair[0].rsplit('--', 1)[1] for pair in pairs] == ['diff', 'report']


def test_the_collected_summary_carries_cost_time_and_models_by_arm(tmp_path):
    batch, protocol, _, fake = _batch(tmp_path)
    for slot in protocol['slots']:
        execute(batch, slot, fake)
    summary = collect(batch)
    assert summary['cost'] == {'diff': 0.02, 'report': 0.02}
    assert summary['mean_output_tokens'] == {'diff': 7, 'report': 7}
    assert summary['models'] == ['claude-sonnet-5-5']
    assert set(summary['mean_seconds']) == {'diff', 'report'}
