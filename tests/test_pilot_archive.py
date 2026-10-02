import json
from pathlib import Path
import subprocess
import sys

import pytest

from eval import challenge, paired


def fixture(tmp_path):
    record = {'schema_version': 1, 'host': 'codex', 'arm': 'baseline', 'replicate': 0, 'state': 'setup',
              'model': 'gpt-6.1-sol', 'effort': 'medium', 'budget_seconds': 240,
              'generated_at': '2026-10-02T00:00:00+00:00', 'identity': challenge.identity(),
              'runtime_fingerprint': 'a'*64, 'elapsed_ms': None, 'exit_code': None,
              'observation': None, 'grade': None, 'mechanisms': {}, 'contract_unchanged': False,
              'error': 'ValueError'}
    protocol = {'schema_version': 1, 'identity': record['identity'], 'models': paired.subscription.MODELS,
                'effort': 'medium', 'seconds_per_run': 240, 'schedule': paired.schedule(),
                'runtime_fingerprint': record['runtime_fingerprint']}
    report_path, protocol_path = tmp_path/'report.json', tmp_path/'protocol.json'
    report_path.write_text(json.dumps({'runs': [record]}))
    protocol_path.write_text(json.dumps(protocol))
    return record, protocol, report_path, protocol_path


def test_archive_cli_reads_only_and_refuses_overwrite(tmp_path):
    record, protocol, report_path, protocol_path = fixture(tmp_path)
    original = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    args = [sys.executable, '-m', 'eval.paired', '--inspect', str(report_path), '--protocol', str(protocol_path)]
    value = subprocess.run(args, text=True, capture_output=True, timeout=20)
    assert value.returncode == 0, value.stderr
    result = json.loads(value.stdout)
    assert result['state'] == 'incomplete' and result['arms'][0]['resolved'] == 0
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == original
    out = tmp_path/'out.json'
    assert subprocess.run([*args, '--output', str(out)], capture_output=True, timeout=20).returncode == 0
    assert subprocess.run([*args, '--output', str(out)], capture_output=True, timeout=20).returncode == 2


def test_archive_private_fields_and_conflicting_modes_rejected(tmp_path):
    record, protocol, report_path, protocol_path = fixture(tmp_path)
    record['prompt'] = 'private'
    with pytest.raises(ValueError):
        paired.summarize([record], protocol=protocol)
    args = [sys.executable, '-m', 'eval.paired', '--inspect', str(report_path), '--protocol', str(protocol_path),
            '--directory', str(tmp_path/'new')]
    assert subprocess.run(args, capture_output=True, timeout=20).returncode == 2
