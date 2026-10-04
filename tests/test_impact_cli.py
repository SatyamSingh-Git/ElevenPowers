"""CLI works without an AI host, implicit writes or a mandatory grammar pack."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_impact.py'


def run(root, *args, stdlib=False):
    return subprocess.run([sys.executable, *(['-S'] if stdlib else []), str(SCRIPT),
                           '--project', str(root), *args], capture_output=True,
                          text=True, timeout=30)


def fixture(root):
    (root / 'session.py').write_text('def expire(): return 1\n')
    (root / 'api.py').write_text('from session import expire\nexpire()\n')


def test_json_and_markdown_queries_without_state_write(tmp_path):
    fixture(tmp_path)
    result = run(tmp_path, 'session.py', '--json')
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['affected'][0]['path'] == 'api.py'
    assert not (tmp_path / '.elevenpowers').exists()
    result = run(tmp_path, 'session.py')
    assert result.returncode == 0
    assert 'api.py' in result.stdout and 'static' in result.stdout


def test_graph_export_and_no_overwrite(tmp_path):
    fixture(tmp_path)
    output = tmp_path / 'graph.txt'
    result = run(tmp_path, '--graph', '--json', '--output', str(output))
    assert result.returncode == 0, result.stderr
    assert json.loads(output.read_text())['schema'] == 1
    before = output.read_bytes()
    result = run(tmp_path, '--graph', '--json', '--output', str(output))
    assert result.returncode == 2
    assert output.read_bytes() == before
    assert run(tmp_path, '--graph', '--json', '--output', str(output), '--force').returncode == 0


def test_check_and_invalid_invocations(tmp_path):
    fixture(tmp_path)
    assert run(tmp_path, 'gone.py', '--check').returncode == 1
    assert run(tmp_path, 'session.py', '--seconds', 'nan').returncode == 2
    assert run(tmp_path, 'session.py', '--max-depth', '21').returncode == 2
    assert run(tmp_path, 'session.py', '--max-files', '0').returncode == 2
    assert run(tmp_path, 'session.py', '--max-bytes', '-1').returncode == 2
    assert run(tmp_path).returncode == 2
    assert run(tmp_path / 'missing', 'a.py').returncode == 2


def test_standard_library_only_query(tmp_path):
    fixture(tmp_path)
    result = run(tmp_path, 'session.py', '--json', stdlib=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['affected']
