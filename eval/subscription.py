"""Explicit subscription-authenticated CLIs; no API fallback or secret exports."""
import json
import os
import re

from core.process import run

MODELS = {'codex': 'gpt-6.1-sol', 'claude': 'claude-sonnet-5-5'}
API_ENV = ('OPENAI_API_KEY', 'CODEX_API_KEY', 'ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN',
           'OPENAI_BASE_URL', 'ANTHROPIC_BASE_URL', 'CLAUDE_CODE_USE_BEDROCK',
           'CLAUDE_CODE_USE_VERTEX', 'CLAUDE_CODE_USE_FOUNDRY')


def auth(host, executable, root):
    if host not in MODELS:
        raise ValueError('only Codex and Claude subscription pilots are supported')
    if any(os.environ.get(key) for key in API_ENV):
        raise ValueError('API environment overrides are not allowed for subscription pilots')
    args = [executable, 'login', 'status'] if host == 'codex' else [executable, 'auth', 'status', '--json']
    result = run(args, cwd=root, timeout=10, shell=False)
    if result.returncode:
        return False
    if host == 'codex':
        return 'logged in using chatgpt' in (result.stdout + result.stderr).lower()
    try:
        value = json.loads(result.stdout)
        return value.get('loggedIn') is True and value.get('authMethod') == 'claude.ai' and value.get('subscriptionType') in ('pro', 'max', 'team', 'enterprise')
    except (ValueError, AttributeError):
        return False


def command(host, executable, root, prompt):
    if host == 'codex':
        return [executable, 'exec', '--ignore-user-config', '--model', MODELS[host],
                '-c', 'model_reasoning_effort="medium"',
                '--approve-for-me', '--ephemeral', '--json', '-C', str(root), prompt]
    if host == 'claude':
        # Prompt precedes variadic tool flags; --bare skips subscription OAuth.
        return [executable, '-p', prompt, '--model', MODELS[host], '--effort', 'medium',
                '--output-format', 'json', '--no-session-persistence', '--no-chrome',
                '--setting-sources', 'project,local', '--permission-mode', 'acceptEdits',
                '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
                '--tools', 'Bash,Read,Edit,Write,Glob,Grep',
                '--allowedTools', 'Bash', 'Read', 'Edit', 'Write', 'Glob', 'Grep']
    raise ValueError('unsupported pilot host')


def observation(host, output, diagnostic=''):
    value = {'completed': False, 'usage': None, 'models': [], 'completion_language': False,
             'failure': 'blocked_by_policy' if 'blocked by policy' in diagnostic.lower() else 'unavailable'}
    try:
        events = [json.loads(line) for line in output.splitlines() if line.strip()] if host == 'codex' else [json.loads(output)]
        text = ''
        for event in events:
            if not isinstance(event, dict):
                raise ValueError('invalid host observation')
            if host == 'codex':
                if event.get('type') == 'turn.completed':
                    value['completed'] = True; usage = event.get('usage')
                elif event.get('type') in ('turn.failed', 'error'):
                    value['completed'] = False; usage = None
                else:
                    usage = None
                item = event.get('item', {})
                if item.get('type') == 'agent_message':
                    text = item.get('text', '')
            else:
                value['completed'] = event.get('is_error') is False
                usage = event.get('usage'); text = event.get('result', '')
                if event.get('api_error_status') == 429:
                    value['failure'] = 'quota_exhausted'
                value['models'] = [key for key in event.get('modelUsage', {})
                                   if re.fullmatch(r'[a-z0-9.-]{1,80}', key)]
            if isinstance(usage, dict):
                value['usage'] = {key: n for key, n in usage.items()
                                  if key in ('input_tokens', 'output_tokens', 'cached_input_tokens',
                                             'cache_read_input_tokens', 'cache_creation_input_tokens', 'reasoning_output_tokens')
                                  and type(n) is int and 0 <= n <= 1_000_000_000}
        value['completion_language'] = bool(re.search(r'\b(done|fixed|completed|implemented)\b', text, re.I))
        if 'blocked by policy' in text.lower():
            value['failure'] = 'blocked_by_policy'
    except (ValueError, TypeError, AttributeError):
        value['completed'] = False
    return value
