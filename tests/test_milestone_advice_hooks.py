"""Documented/replayed transports, not installed-host acceptance."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from core.ledger import Ledger
from core.obligations import Claim
from test_milestone_advice_worker import opted


def edit_payload(root):
    return {'cwd': str(root), 'tool_name': 'Write',
            'tool_input': {'file_path': str(root / 'cli.py')}, 'tool_response': {'exit_code': 0}}


def test_direct_claude_edit_returns_one_json_object_with_guidance_and_advice(tmp_path):
    ledger = opted(tmp_path)
    ledger.claims = [Claim.FEATURE_ADDED]; ledger.save()
    code = Path(__file__).resolve().parents[1]
    done = subprocess.run([sys.executable, '-m', 'core.hook', 'PostToolUse'], cwd=code,
        input=json.dumps(edit_payload(tmp_path)), capture_output=True, text=True, timeout=20)
    assert done.returncode == 0, done.stderr
    output = json.loads(done.stdout)  # multiple JSON objects must fail
    context = output['hookSpecificOutput']['additionalContext']
    assert 'milestone advice' in context
    assert Ledger.load(tmp_path).guided
    assert Ledger.load(tmp_path).evidence == []


@pytest.mark.parametrize('host,event,field', [
    ('codex', 'PostToolUse', 'additionalContext'),
    ('gemini', 'AfterTool', 'additionalContext'),
    ('cursor', 'postToolUse', 'additional_context'),
    ('copilot', 'postToolUse', 'additionalContext')])
def test_shared_edit_advice_survives_native_transport(tmp_path, host, event, field):
    from core.hosts.bridge import run
    opted(tmp_path)
    payload = edit_payload(tmp_path)
    if host == 'gemini':
        payload['tool_name'] = 'write_file'
    if host == 'copilot':
        payload['toolName'] = 'create'
        payload['toolArgs'] = {'file_path': str(tmp_path / 'cli.py')}
    response, code = run(host, event, payload)
    assert code == 0
    assert 'milestone advice' in json.dumps(response), response
    assert field in json.dumps(response)
    assert Ledger.load(tmp_path).evidence == []


def test_off_and_unconfigured_hooks_do_not_launch_advice(tmp_path, monkeypatch):
    from core import hook
    import core.milestones.automatic as automatic
    ledger = opted(tmp_path)
    (tmp_path / '.elevenpowers/config.json').write_text('{"profile":"off"}')
    def forbidden(*args, **kwargs):
        pytest.fail('passive project launched worker')
    monkeypatch.setattr(automatic, 'run', forbidden)
    assert hook.on_post_tool(edit_payload(tmp_path), tmp_path) == 0
    assert not (tmp_path / '.elevenpowers/advice.json').exists()
