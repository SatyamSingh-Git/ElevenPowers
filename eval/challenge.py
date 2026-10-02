"""Frozen original behavioral task; independent evaluator stays outside candidates."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from core.process import run

PROMPT = '''Repair bank.engine.apply_batch for the contract below. Work only inside this project.
Keep existing public APIs and all tests unchanged. You may edit production bank/*.py files.
Run python visible.py before completing; report honestly any incomplete work.

apply_batch(balances, journal, entries) mutates the two dictionaries only when
the entire batch succeeds and returns one status per entry: applied or replayed.
Each entry has exactly id, from, to, amount. IDs/accounts are nonempty strings;
amount is a positive integer (booleans are invalid). Accounts must already exist.
Balances are nonnegative integers (booleans are invalid). Validate the whole batch
as it executes on private working state. Any invalid entry, unknown account,
insufficient funds or conflicting reuse of an id raises ValueError and leaves
both input dictionaries exactly unchanged, including earlier entries in the batch.
Journal maps an id to its (from, to, amount) tuple. An identical existing id is
replayed without moving money, even if funds are now insufficient. Conflicting
reuse fails. Duplicate IDs within a batch follow the same rules. A self-transfer
requires sufficient funds but leaves its balance unchanged and is journaled.
An empty batch returns []. Preserve bank.view.total and statement behavior.
'''
BUGGY = '''def apply_batch(balances, journal, entries):
    result = []
    for e in entries:
        if e['id'] in journal:
            result.append('replayed')
            continue
        balances[e['from']] -= e['amount']
        balances[e['to']] += e['amount']
        journal[e['id']] = (e['from'], e['to'], e['amount'])
        result.append('applied')
    return result
'''
GOLD = '''def apply_batch(balances, journal, entries):
    if any(type(v) is not int or v < 0 for v in balances.values()):
        raise ValueError('invalid balances')
    work, history = balances.copy(), journal.copy()
    statuses = []
    for e in entries:
        if (not isinstance(e, dict) or set(e) != {'id', 'from', 'to', 'amount'} or
                any(not isinstance(e[k], str) or not e[k] for k in ('id', 'from', 'to')) or
                type(e['amount']) is not int or e['amount'] <= 0):
            raise ValueError('invalid entry')
        source, target, amount = e['from'], e['to'], e['amount']
        if source not in work or target not in work:
            raise ValueError('unknown account')
        signature = (source, target, amount)
        if e['id'] in history:
            if history[e['id']] != signature:
                raise ValueError('conflicting id')
            statuses.append('replayed')
            continue
        if work[source] < amount:
            raise ValueError('insufficient funds')
        work[source] -= amount
        work[target] += amount
        history[e['id']] = signature
        statuses.append('applied')
    balances.clear(); balances.update(work)
    journal.clear(); journal.update(history)
    return statuses
'''
VISIBLE = '''from bank.engine import apply_batch
from bank.view import total, statement
b, j = {'a': 12, 'b': 3}, {}
assert apply_batch(b, j, [{'id': 'x', 'from': 'a', 'to': 'b', 'amount': 2}]) == ['applied']
assert b == {'a': 10, 'b': 5} and total(b) == 15
assert statement(b) == [('a', 10), ('b', 5)]
print('TAP version 13\\n1..1\\nok 1 - public smoke\\n# tests 1\\n# pass 1\\n# fail 0')
'''
FILES = {'bank/__init__.py': '', 'bank/engine.py': BUGGY,
         'bank/view.py': 'def total(balances):\n    return sum(balances.values())\n\ndef statement(balances):\n    return sorted(balances.items())\n',
         'visible.py': VISIBLE, 'TASK.txt': PROMPT, '.gitignore': '__pycache__/\n.elevenpowers/\n.claude/\n.codex/\n'}


def _digest(values):
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def identity():
    grader = Path(__file__).with_name('challenge_grader.py').read_bytes()
    return {'task': _digest(FILES), 'prompt': hashlib.sha256(PROMPT.encode()).hexdigest(),
            'grader': hashlib.sha256(grader).hexdigest()}


def prepare(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    for name, body in FILES.items():
        path = root / name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding='utf-8')
    return identity()


def contract(root):
    root = Path(root).resolve()
    try:
        return all(not (root / name).is_symlink() and (root / name).resolve().is_relative_to(root) and
                   (root / name).read_text(encoding='utf-8') == body
                   for name, body in FILES.items() if name not in ('bank/engine.py', 'bank/view.py'))
    except (OSError, UnicodeError):
        return False


def grade(root):
    try:
        result = run([sys.executable, '-I', str(Path(__file__).with_name('challenge_grader.py')), str(Path(root).resolve())],
                     cwd=Path(root), timeout=15, shell=False)
        value = json.loads(result.stdout)
        if result.returncode or set(value) != {'state', 'passed', 'total', 'regressions', 'checks'}:
            raise ValueError('invalid grader response')
        if (value['state'] != 'graded' or type(value['total']) is not int or value['total'] != 16 or
                type(value['passed']) is not int or not 0 <= value['passed'] <= 16 or
                type(value['regressions']) is not int or not 0 <= value['regressions'] <= 4 or
                not isinstance(value['checks'], dict) or len(value['checks']) != 16 or
                any(type(v) is not bool for v in value['checks'].values()) or
                value['passed'] != sum(value['checks'].values())):
            raise ValueError('invalid behavioral grade')
        return value
    except (OSError, ValueError, subprocess.SubprocessError):
        return {'state': 'setup', 'passed': 0, 'total': 0, 'regressions': None, 'checks': {}}
