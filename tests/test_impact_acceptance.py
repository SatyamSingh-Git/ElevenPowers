"""Independent execution verifies usefulness of graph-selected cross-component checks."""
import json
import subprocess
import sys

from core.impact import analyze, build


def put(root, path, text):
    file = root / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text, encoding='utf-8')


def prepare(root):
    put(root, 'session.py', 'def expired(now, deadline, grace=0):\n    return now >= deadline + grace\n')
    put(root, 'api.py', 'from session import expired as is_expired\ndef login(now, deadline):\n    return 401 if is_expired(now, deadline) else 200\n')
    put(root, 'worker.py', 'import session\ndef cleanup(records, now):\n    return [key for key, deadline in records.items() if session.expired(now, deadline)]\n')
    put(root, 'unrelated.py', 'def expired():\n    return "not a session"\n')
    put(root, 'tests/__init__.py', '')
    put(root, 'tests/test_api.py', '''import unittest
from api import login
class LoginContract(unittest.TestCase):
    def test_boundary_is_rejected(self):
        self.assertEqual(login(100, 100), 401)
    def test_future_session_is_accepted(self):
        self.assertEqual(login(99, 100), 200)
''')
    put(root, 'tests/test_worker.py', '''import unittest
from worker import cleanup
class WorkerContract(unittest.TestCase):
    def test_expired_and_boundary_removed(self):
        self.assertEqual(cleanup({"old":99,"boundary":100,"future":101}, 100), ["old","boundary"])
    def test_empty_input_stays_empty(self):
        self.assertEqual(cleanup({}, 100), [])
''')
    put(root, 'impactgraph.json', json.dumps({'schema': 1, 'nodes': [
        {'id': 'route:login', 'kind': 'route', 'label': 'POST /login', 'path': 'api.py'},
        {'id': 'database:session-retention', 'kind': 'database', 'label': 'session retention'}],
        'edges': [{'source': 'route:login', 'target': 'file:api.py', 'kind': 'uses'},
                  {'source': 'database:session-retention', 'target': 'file:session.py', 'kind': 'depends_on'}]}))


def execute(root, selected):
    return subprocess.run([sys.executable, '-B', '-S', '-m', 'unittest',
                           *[p[:-3].replace('/', '.') for p in selected], '-v'],
                          cwd=root, capture_output=True, text=True, timeout=30)


def test_selected_consumers_catch_regression_and_accept_equivalent_change(tmp_path):
    prepare(tmp_path)
    result = analyze(build(tmp_path), ['session.py'])
    ids = {n['id'] for n in result['affected']}
    assert {'file:api.py', 'file:worker.py', 'route:login', 'database:session-retention'} <= ids
    assert 'file:unrelated.py' not in ids
    selected = sorted({n['path'] for n in result['tests']})
    assert selected == ['tests/test_api.py', 'tests/test_worker.py']
    correct = execute(tmp_path, selected)
    assert correct.returncode == 0, correct.stderr
    # Independent boundary fault: neither AST nor the graph grades behavior.
    put(tmp_path, 'session.py', 'def expired(now, deadline, grace=0):\n    return now > deadline + grace\n')
    defective = execute(tmp_path, selected)
    assert defective.returncode == 1
    assert 'test_boundary_is_rejected' in defective.stderr
    assert 'test_expired_and_boundary_removed' in defective.stderr
    assert 'FAILED (failures=2)' in defective.stderr
    put(tmp_path, 'session.py', 'def expired(now, deadline, grace=0):\n    return not now < deadline + grace\n')
    equivalent = execute(tmp_path, selected)
    assert equivalent.returncode == 0, equivalent.stderr
    assert 'Ran 4 tests' in equivalent.stderr
