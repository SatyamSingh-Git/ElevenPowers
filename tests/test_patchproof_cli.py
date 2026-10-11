import json
from pathlib import Path
import subprocess
import sys

from tests.test_patchproof_report import project, seed


CLI = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_patchproof.py'


def invoke(root, base, head, *args):
    return subprocess.run([sys.executable, str(CLI), '--project', str(root),
                           '--base', base, '--head', head, *args], capture_output=True,
                          text=True, timeout=30)


def test_cli_json_and_markdown_preserve_binding_and_identity(project):
    root, base, head = project
    seed(root)
    exported = invoke(root, base, head, '--format', 'json', '--require-bound')
    assert exported.returncode == 0, exported.stderr
    value = json.loads(exported.stdout)
    readable = invoke(root, base, head)
    assert readable.returncode == 0
    assert value['patch']['patch_id'] in readable.stdout
    assert head in readable.stdout and base in readable.stdout
    assert 'UNVERIFIED' in readable.stdout
    assert 'Unsigned' in readable.stdout
    assert 'API compatibility' in readable.stdout
    assert 'private prompt' not in readable.stdout


def test_cli_atomic_output_refuses_overwrite_without_force(project, tmp_path):
    root, base, head = project
    seed(root)
    output = root.parent / (root.name + '-bundle.json')
    first = invoke(root, base, head, '--format', 'json', '--output', str(output))
    assert first.returncode == 0, first.stderr
    output.write_text('original')
    assert invoke(root, base, head, '--output', str(output)).returncode == 1
    assert output.read_text() == 'original'
    assert invoke(root, base, head, '--format', 'json', '--output', str(output), '--force').returncode == 0
    assert json.loads(output.read_text())['kind'] == 'patchproof'


def test_cli_binding_gate_and_empty_project_are_honest(project, tmp_path):
    root, base, head = project
    seed(root)
    (root / 'service.py').write_bytes(b'value=999\n')
    value = invoke(root, base, head, '--format', 'json', '--require-bound')
    assert value.returncode == 1
    assert json.loads(value.stdout)['binding']['state'] == 'unavailable'
    missing = invoke(root, 'unknown-ref', head, '--format', 'json')
    assert missing.returncode == 0
    assert not json.loads(missing.stdout)['patch']['complete']


def test_cli_escapes_markdown_from_receipt_and_never_executes_commands(project):
    root, base, head = project
    seed(root, command='<script> | `bad`\nnext')
    (root / '.elevenpowers/config.json').write_text(json.dumps({
        'auto_detect': False, 'commands': {'build': 'echo unsafe > should-not-exist'}}))
    exported = invoke(root, base, head)
    assert exported.returncode == 0
    assert '<script>' not in exported.stdout
    assert not (root / 'should-not-exist').exists()

