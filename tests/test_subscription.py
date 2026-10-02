import json
from types import SimpleNamespace

import pytest

from eval import subscription


def test_exact_models_and_equal_effort_no_bypass(tmp_path):
    for host, model in [('codex', 'gpt-6.1-sol'), ('claude', 'claude-sonnet-5-5')]:
        args = subscription.command(host, 'host.exe', tmp_path, 'PROMPT')
        assert model in args and 'medium' in str(args)
        assert not any('bypass' in arg or arg == '--bare' for arg in args)
        assert 'PROMPT' in args


def test_subscription_auth_and_api_refusal(monkeypatch, tmp_path):
    monkeypatch.setattr(subscription, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout='Logged in using ChatGPT', stderr=''))
    monkeypatch.setattr(subscription.os, 'environ', {})
    assert subscription.auth('codex', 'host', tmp_path)
    monkeypatch.setattr(subscription.os, 'environ', {'OPENAI_API_KEY': 'private'})
    with pytest.raises(ValueError, match='API'):
        subscription.auth('codex', 'host', tmp_path)
    monkeypatch.setattr(subscription.os, 'environ', {})
    monkeypatch.setattr(subscription, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps({'loggedIn': True, 'authMethod': 'claude.ai', 'subscriptionType': 'max', 'private': 'secret'}), stderr=''))
    assert subscription.auth('claude', 'host', tmp_path)
    monkeypatch.setattr(subscription, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout='API key', stderr=''))
    assert not subscription.auth('codex', 'host', tmp_path)


def test_usage_unavailable_and_error_not_completion():
    assert subscription.observation('codex', '')['completed'] is False
    codex = '\n'.join(json.dumps(x) for x in [
        {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'private'}},
        {'type': 'turn.completed', 'usage': {'input_tokens': 3, 'output_tokens': 4}}])
    value = subscription.observation('codex', codex)
    assert value['completed'] and value['usage']['input_tokens'] == 3
    assert 'private' not in str(value)
    assert not subscription.observation('claude', '{"is_error": true, "result": "private"}')['completed']
