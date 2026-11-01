"""The reviewer study's prompt, answer reading and grading, fixed before any model call."""
import json

from eval.reviewer_study import analyse, answer, grade, prompt

W = {'kind': 'W', 'path': 'src/pkg/mod.py', 'line': 40, 'end_line': 41}


def _reply(decision='request_changes', **problem):
    return {'decision': decision, 'problems': [problem] if problem else []}


def test_only_the_report_arm_sees_the_report():
    assert 'REPORT-TEXT' in prompt('do x', 'DIFF', 'REPORT-TEXT')
    plain = prompt('do x', 'DIFF')
    assert 'REPORT-TEXT' not in plain and 'report' not in plain.lower()
    assert 'do x' in plain and 'DIFF' in plain


def test_the_answer_is_the_json_object_in_the_reply():
    body = {'decision': 'accept', 'problems': []}
    assert answer('Here it is:\n```json\n' + json.dumps(body) + '\n```') == body
    assert answer('no json here') is None
    assert answer('} reversed {') is None and answer('{ never closed') is None
    assert answer(json.dumps({'decision': 'maybe', 'problems': []})) is None
    assert answer(json.dumps({'decision': 'accept', 'problems': 'none'})) is None


def test_a_wrong_line_is_caught_only_by_naming_its_file_near_its_line():
    assert grade(W, _reply(file='src/pkg/mod.py', line=42, kind='wrong_behaviour'))
    assert grade(W, _reply(file='b/src/pkg/mod.py', line=38, kind='other'))
    assert grade(W, _reply(file='pkg/mod.py', line=40, kind='wrong_behaviour'))
    assert not grade(W, _reply(file='src/pkg/mod.py', line=44, kind='wrong_behaviour'))
    assert not grade(W, _reply(file='src/pkg/mod.py', line=37, kind='wrong_behaviour'))
    assert not grade(W, _reply(file='src/pkg/other.py', line=40, kind='wrong_behaviour'))
    assert not grade(W, _reply(file='g/mod.py', line=40, kind='wrong_behaviour'))
    assert not grade(W, _reply(file='src/pkg/mod.py', line='40', kind='wrong_behaviour'))


def test_an_untested_change_is_caught_by_asking_for_a_test():
    seed = {'kind': 'U'}
    assert grade(seed, _reply(file='tests/x.py', line=1, kind='missing_test'))
    assert not grade(seed, _reply('accept', file='tests/x.py', line=1, kind='missing_test'))
    assert not grade(seed, _reply(file='src/a.py', line=1, kind='wrong_behaviour'))


def test_a_control_counts_a_request_for_changes_as_a_false_alarm():
    assert grade({'kind': 'C'}, _reply())
    assert not grade({'kind': 'C'}, _reply('accept'))


def test_an_unreadable_reply_is_not_scored():
    assert grade(W, None) is None


def test_the_analysis_pairs_each_seed_across_arms():
    rows = [{'seed': f's{n}', 'kind': 'W', 'arm': arm, 'caught': caught}
            for n, pair in enumerate([(False, True)] * 6 + [(True, True), (False, False), (True, False)])
            for arm, caught in zip(('diff', 'report'), pair)]
    rows.append({'seed': 'lost', 'kind': 'W', 'arm': 'report', 'caught': True})
    rows += [{'seed': 'unread', 'kind': 'W', 'arm': 'diff', 'caught': True},
             {'seed': 'unread', 'kind': 'W', 'arm': 'report', 'caught': None}]
    result = analyse(rows)['W']
    assert result['caught'] == {'diff': 2, 'report': 7}
    assert result['report_only'] == 6 and result['diff_only'] == 1 and result['pairs'] == 9
    assert result['p'] == 2 * (1 + 7) / 2 ** 7
    assert result['unpaired'] == 2
