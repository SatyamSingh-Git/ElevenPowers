import json
from pathlib import Path
import subprocess
import sys


SCRIPT = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_validate.py'


def test_matrix_cli_and_atomic_output(tmp_path):
    out = tmp_path / 'matrix.json'
    args = [sys.executable, str(SCRIPT), 'matrix', '--json', '--output', str(out), '--check']
    result = subprocess.run(args, capture_output=True, text=True, timeout=20)
    assert result.returncode == 1
    value = json.loads(out.read_text())
    assert value['passed'] == 0 and value['total'] == 10
    original = out.read_bytes()
    assert subprocess.run(args, capture_output=True, timeout=20).returncode == 2
    assert out.read_bytes() == original


def test_cli_rejects_invalid_input_and_unknown_flags(tmp_path):
    bad = tmp_path / 'bad.json'; bad.write_text('{"schema_version": NaN}')
    for args in (['matrix', str(bad)], ['capture', 'codex'], ['matrix', '--unexpected']):
        assert subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, timeout=20).returncode == 2
