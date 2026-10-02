"""Frozen assertions run in a controller that never imports candidate code."""
import json
from pathlib import Path
import sys

CHECK_NAMES = ('basic_transfer', 'empty', 'repeat', 'replay_without_funds', 'conflicting_id',
               'insufficient', 'batch_atomicity', 'unknown_account', 'self_transfer',
               'self_requires_funds', 'invalid_amounts', 'invalid_ids', 'malformed_entries',
               'invalid_balances', 'view_total', 'view_statement')


def main(root):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from core.process import run
    from eval.challenge_worker import encode
    groups, requests, expected = {}, [], []
    def entry(key='x', amount=2, source='a', target='b'):
        return {'id': key, 'from': source, 'to': target, 'amount': amount}
    def add(name, entries, statuses=None, after=None, history=None, balances=None, journal=None, reject=False):
        b = balances if balances is not None else {'a': 10, 'b': 0}
        j = journal if journal is not None else {}
        index = len(requests)
        requests.append({'operation': 'apply', 'balances': b, 'journal': j, 'entries': entries})
        expected.append(encode({'result': None if reject else statuses, 'exception': 'ValueError' if reject else '',
                                'balances': b if reject else after, 'journal': j if reject else history}))
        groups.setdefault(name, []).append(index)
    add('basic_transfer', [entry()], ['applied'], {'a': 8, 'b': 2}, {'x': ('a', 'b', 2)})
    add('empty', [], [], {'a': 10, 'b': 0}, {})
    add('repeat', [entry(), entry()], ['applied', 'replayed'], {'a': 8, 'b': 2}, {'x': ('a', 'b', 2)})
    add('replay_without_funds', [entry()], ['replayed'], {'a': 0, 'b': 10}, {'x': ('a', 'b', 2)},
        {'a': 0, 'b': 10}, {'x': ('a', 'b', 2)})
    for name, entries in [('conflicting_id', [entry(), entry(amount=3)]), ('insufficient', [entry(amount=11)]),
                          ('batch_atomicity', [entry(), entry(key='y', amount=9)]),
                          ('unknown_account', [entry(), entry(key='y', target='missing')]),
                          ('self_requires_funds', [entry(target='a', amount=11)])]:
        add(name, entries, reject=True)
    add('self_transfer', [entry(target='a')], ['applied'], {'a': 10, 'b': 0}, {'x': ('a', 'a', 2)})
    for amount in (True, 0, -1, 1.5, '2'):
        add('invalid_amounts', [entry(), entry(key='y', amount=amount)], reject=True)
    for key in ('', 2, None):
        add('invalid_ids', [entry(key=key)], reject=True)
    for item in ({}, None, {**entry(), 'extra': 1}):
        add('malformed_entries', [entry(), item], reject=True)
    for balance in (True, -1, 1.2):
        add('invalid_balances', [], balances={'a': balance, 'b': 0}, reject=True)
    for name, operation, answer in [('view_total', 'total', 7), ('view_statement', 'statement', [('a', 2), ('b', 5)])]:
        groups[name] = [len(requests)]
        requests.append({'operation': operation, 'balances': {'b': 5, 'a': 2}})
        expected.append(encode({'result': answer, 'exception': ''}))
    result = run([sys.executable, '-I', str(Path(__file__).with_name('challenge_worker.py')), str(root),
                  json.dumps(requests, allow_nan=False)], cwd=root, timeout=10, shell=False)
    observed = json.loads(result.stdout)
    if result.returncode or not isinstance(observed, dict) or set(observed) != {'responses'}:
        raise ValueError('invalid candidate behavior response')
    responses = observed['responses']
    if not isinstance(responses, list) or len(responses) != len(requests):
        raise ValueError('incomplete candidate behavior response')
    checks = {name: all(responses[i] == expected[i] for i in groups[name]) for name in CHECK_NAMES}
    return {'state': 'graded', 'passed': sum(checks.values()), 'total': len(checks),
            'regressions': sum(not checks[k] for k in ('view_total', 'view_statement', 'basic_transfer', 'empty')),
            'checks': checks}


if __name__ == '__main__':
    print(json.dumps(main(Path(sys.argv[1]).resolve()), allow_nan=False))
