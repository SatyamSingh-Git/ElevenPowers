"""Existing declared edges close explicit process boundaries, never infer them."""
import json
import subprocess
import sys

from core.milestones import build


def process_project(root):
    (root / 'cli.py').write_text('print(3)\n')
    (root / 'test_cli.py').write_text(
        'import subprocess, sys\n'
        'def test_cli():\n'
        '    assert subprocess.check_output([sys.executable, "cli.py"], text=True).strip() == "3"\n')
    (root / 'other.py').write_text('value = 9\n')
    (root / 'elevenpowers.milestones.json').write_text(json.dumps({'schema': 1, 'milestones': [
        {'id': 'cli', 'description': 'CLI returns three', 'inputs': ['test_cli.py'],
         'checks': [{'kind': 'test_suite', 'command': 'python -m pytest test_cli.py -q'}]},
        {'id': 'other', 'description': 'Other behavior', 'inputs': ['other.py'],
         'checks': [{'kind': 'test_suite', 'command': 'python -m pytest other.py -q'}]}]}))
    return root


def test_explicit_process_boundary_has_declared_provenance_and_keeps_fallback(tmp_path):
    root = process_project(tmp_path)
    before = build(root, impact=True, changed=['cli.py'])
    assert not before['impact']['leads']  # subprocess is deliberately not inferred
    (root / 'impactgraph.json').write_text(json.dumps({'schema': 1, 'edges': [
        {'source': 'file:test_cli.py', 'target': 'file:cli.py', 'kind': 'uses'}]}))
    after = build(root, impact=True, changed=['cli.py'])
    assert after['rechecks']['commands'][0]['priority'] == 'dependency'
    reason = after['rechecks']['commands'][0]['reasons'][0]
    assert reason['milestone'] == 'cli' and reason['category'] == 'declared'
    assert reason['explanation'][0]['origin'] == 'declared'
    assert after['rechecks']['commands'][1]['priority'] == 'fallback'
    assert after['rechecks']['safe_to_exclude'] is False
    for source, expected in [('print(3)\n', 0), ('print(4)\n', 1), ('print(1 + 2)\n', 0)]:
        (root / 'cli.py').write_text(source)
        done = subprocess.run([sys.executable, '-m', 'pytest', 'test_cli.py', '-q'],
                              cwd=root, capture_output=True, text=True, timeout=30)
        assert done.returncode == expected, done.stdout + done.stderr


def test_invalid_declared_endpoint_cannot_establish_a_process_relationship(tmp_path):
    root = process_project(tmp_path)
    (root / 'impactgraph.json').write_text(json.dumps({'schema': 1, 'edges': [
        {'source': 'file:test_cli.py', 'target': 'file:missing.py', 'kind': 'uses'}]}))
    value = build(root, impact=True, changed=['cli.py'])
    assert value['rechecks']['state'] == 'incomplete'
    assert not value['impact']['leads']
    assert all(c['priority'] == 'fallback' for c in value['rechecks']['commands'])
