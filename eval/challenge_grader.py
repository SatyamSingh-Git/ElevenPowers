"""Independent frozen behavioral evaluator. Run only in a contained child."""
import copy
import importlib.util
import json
from pathlib import Path
import sys


def main(root):
    modules = {}
    for name in ('engine', 'view'):
        path = root / 'bank' / (name + '.py')
        if path.is_symlink() or not path.resolve().is_relative_to(root) or path.stat().st_size > 128*1024:
            raise ValueError('invalid candidate source')
        spec = importlib.util.spec_from_file_location('candidate_' + name, path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        modules[name] = module
    apply = modules['engine'].apply_batch
    checks = {}
    def check(name, function):
        try:
            checks[name] = bool(function())
        except Exception:
            checks[name] = False
    def entry(key='x', amount=2, source='a', target='b'):
        return {'id': key, 'from': source, 'to': target, 'amount': amount}
    def valid(entries, expected, balances=None, journal=None):
        b = balances if balances is not None else {'a': 10, 'b': 0}
        j = journal if journal is not None else {}
        statuses = apply(b, j, entries)
        return (statuses, b, j) == expected
    def rejected(entries, balances=None, journal=None):
        b = balances if balances is not None else {'a': 10, 'b': 0}
        j = journal if journal is not None else {}
        old = copy.deepcopy((b, j))
        try:
            apply(b, j, entries)
        except ValueError:
            return (b, j) == old
        return False
    check('basic_transfer', lambda: valid([entry()], (['applied'], {'a': 8, 'b': 2}, {'x': ('a', 'b', 2)})))
    check('empty', lambda: valid([], ([], {'a': 10, 'b': 0}, {})))
    check('repeat', lambda: valid([entry(), entry()], (['applied', 'replayed'], {'a': 8, 'b': 2}, {'x': ('a', 'b', 2)})))
    check('replay_without_funds', lambda: valid([entry()], (['replayed'], {'a': 0, 'b': 10}, {'x': ('a', 'b', 2)}), {'a': 0, 'b': 10}, {'x': ('a', 'b', 2)}))
    check('conflicting_id', lambda: rejected([entry(), entry(amount=3)]))
    check('insufficient', lambda: rejected([entry(amount=11)]))
    check('batch_atomicity', lambda: rejected([entry(), entry(key='y', amount=9)]))
    check('unknown_account', lambda: rejected([entry(), entry(key='y', target='missing')]))
    check('self_transfer', lambda: valid([entry(target='a')], (['applied'], {'a': 10, 'b': 0}, {'x': ('a', 'a', 2)})))
    check('self_requires_funds', lambda: rejected([entry(target='a', amount=11)]))
    check('invalid_amounts', lambda: all(rejected([entry(), entry(key='y', amount=v)]) for v in (True, 0, -1, 1.5, '2')))
    check('invalid_ids', lambda: all(rejected([entry(key=v)]) for v in ('', 2, None)))
    check('malformed_entries', lambda: all(rejected([entry(), e]) for e in ({}, None, {**entry(), 'extra': 1})))
    check('invalid_balances', lambda: all(rejected([], {'a': v, 'b': 0}) for v in (True, -1, 1.2)))
    check('view_total', lambda: modules['view'].total({'a': 2, 'b': 5}) == 7)
    check('view_statement', lambda: modules['view'].statement({'b': 5, 'a': 2}) == [('a', 2), ('b', 5)])
    return {'state': 'graded', 'passed': sum(checks.values()), 'total': len(checks),
            'regressions': sum(not checks[k] for k in ('view_total', 'view_statement', 'basic_transfer', 'empty')),
            'checks': checks}


if __name__ == '__main__':
    print(json.dumps(main(Path(sys.argv[1]).resolve()), allow_nan=False))
