"""Explicit disposable native exercises; preparation is never live acceptance."""
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import time
import uuid

from ..config import Config, save
from ..process import run
from .readiness import activation, signature
from .diagnostics import read_json
from .setup import PATHS, config_path, install

PYTHON_SOURCE = 'def accepts(value):\n    return value > 10\n'
PYTHON_TEST = '''import time
import unittest
from pathlib import Path
from app import accepts

class Boundary(unittest.TestCase):
    def test_contract(self):
        self.assertFalse(accepts(9))
        self.assertTrue(accepts(10))
        self.assertTrue(accepts(11))

if Path('wait.flag').exists():
    print('Waiting for intentional interruption', flush=True)
    time.sleep(60)
result = unittest.TestResult()
unittest.defaultTestLoader.loadTestsFromTestCase(Boundary).run(result)
failed = len(result.failures) + len(result.errors)
print('TAP version 13')
print('1..1')
print(('not ok' if failed else 'ok') + ' 1 - stated boundary contract')
print('# tests', result.testsRun)
print('# pass', result.testsRun - failed)
print('# fail', failed)
raise SystemExit(1 if failed or result.testsRun != 1 else 0)
'''
JS_SOURCE = 'export function accepts(value) { return value > 10; }\n'
JS_TEST = '''import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { accepts } from './app.mjs';
test('stated boundary contract', async () => {
  if (existsSync('wait.flag')) {
    console.log('Waiting for intentional interruption');
    await new Promise(resolve => setTimeout(resolve, 60000));
  }
  assert.equal(accepts(9), false);
  assert.equal(accepts(10), true);
  assert.equal(accepts(11), true);
});
'''


def prepare(host, destination, language, source, version='', *, advice=False):
    if host not in PATHS:
        raise ValueError('unsupported host')
    if language not in ('python', 'javascript'):
        raise ValueError('unsupported acceptance language')
    if type(advice) is not bool:
        raise ValueError('advice selection must be boolean')
    if not isinstance(version, str) or len(version) > 128 or '\n' in version:
        raise ValueError('invalid operator host version')
    requested = Path(destination).absolute()
    if requested.is_symlink() or requested.exists():
        raise ValueError('acceptance destination already exists or is linked')
    if any(p.is_symlink() for p in requested.parents):
        raise ValueError('linked acceptance destination parent is unsupported')
    root = requested.resolve()
    root.parent.mkdir(parents=True, exist_ok=True)
    runtime = sys.executable if language == 'python' else shutil.which('node')
    if not runtime:
        raise ValueError('Node runtime unavailable; install it before preparing JavaScript acceptance')
    source = Path(source).resolve(strict=True)
    from .provenance import fingerprint
    runtime_fingerprint = fingerprint(source)
    root.mkdir()
    app, test = ('app.py', 'check.py') if language == 'python' else ('app.mjs', 'check.test.mjs')
    (root / app).write_text(PYTHON_SOURCE if language == 'python' else JS_SOURCE, encoding='utf-8')
    (root / test).write_text(PYTHON_TEST if language == 'python' else JS_TEST, encoding='utf-8')
    (root / '.gitignore').write_text('.elevenpowers/\nwait.flag\n__pycache__/\n', encoding='utf-8')
    command = f'"{runtime}" ' + ('check.py' if language == 'python' else '--test check.test.mjs')
    save(root, Config(profile='guide', commands={'tests': command}, auto_detect=False, strength={'enabled': False},
                      milestone_advice=({'enabled': True, 'seconds': 2, 'cooldown': 0, 'max_attempts': 3}
                                        if advice else {})))
    if advice:
        declarations = {'schema': 1, 'milestones': [
            {'id': 'boundary', 'description': 'Values below ten are rejected; ten and above are accepted.',
             'inputs': [app, test], 'checks': [{'kind': 'test_suite', 'command': command}]}]}
        (root / 'elevenpowers.milestones.json').write_text(json.dumps(declarations, indent=2) + '\n', encoding='utf8')
    install(host, root, sys.executable, source)
    for args in (['init', '-q'], ['add', app, test, '.gitignore'],
                 ['-c', 'user.email=acceptance@example.invalid', '-c', 'user.name=ElevenPowers acceptance',
                  'commit', '-qm', 'Intentionally failing boundary exercise']):
        done = run(['git', '-c', f'safe.directory={root.as_posix()}', *args], cwd=root, timeout=10, shell=False)
        if done.returncode:
            raise ValueError('Acceptance Git preparation failed; choose a new destination after inspecting this one')
    value = {'schema_version': 1, 'state': 'prepared', 'exercise': uuid.uuid4().hex, 'host': host,
             'language': language, 'source_file': app, 'test_file': test, 'command': command,
             'prepared_at': time.time(), 'host_version': version or 'unavailable',
             'runtime_fingerprint': runtime_fingerprint,
             'version_source': 'operator' if version else 'unavailable',
             'generation': activation(host, root)['generation'],
             'configuration': signature(config_path(host, root)),
             'project_configuration': signature(root / '.elevenpowers/config.json'),
             'initial_source': signature(root / app), 'test_fingerprint': signature(root / test)}
    if advice:
        value.update(advice_requested=True, milestone_declaration=signature(root / 'elevenpowers.milestones.json'))
    (root / '.elevenpowers/acceptance.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    instructions = f'''# Native acceptance exercise: {host} / {language}

Preparation has not started a host or established native acceptance. Use a new
installed {host} session in this directory and review its ordinary hook trust.
Record the exact host version; an operator version is metadata, not attestation.

Use one task/session for this exercise. Ask the host to:

1. Run the declared test command below and observe its real failure.
2. Fix only `{app}` so `accepts` is false below 10 and true at or above 10.
3. Run the same command and observe its real success.
4. Create `wait.flag`, run the same command with a short timeout or deliberately
   interrupt it, and observe incomplete execution. Remove `wait.flag` afterward.
5. Edit a source comment, then inspect readiness to see stale evidence.
6. Rerun the declared command and finish normally, delivering completion.

Run the declared command as its own tool call, exactly as written, from this
directory. One supported literal prefix is also allowed:
`cd "{root.as_posix()}" && {command}`. Keep helper commands separate. Arbitrary
prefixes, suffixes such as `; echo $?`, pipelines and timeout wrappers change
the declared command and may hide its exit status. Use quoted forward-slash
absolute paths or `cd . &&`; parent traversal and shell expansion are unsupported.
For the interrupted step use the host tool's timeout
or interrupt control on the same standalone command. Do not rewrite declarations
to make this exercise pass. End with the factual result of the exercise.

```text
{command}
```

Keep `{test}`, project configuration and native wiring unchanged. Do not send
fabricated hook payloads or use replay to establish acceptance. The exercise uses
real unittest/Node tests and downloads no packages. An installed agent session may
consume the host's normal model allowance; preparation itself makes no model call.

After completion, inspect the result from a separate terminal:

```text
python "{source / 'plugin/bin/ep_doctor.py'}" --acceptance "{root}" --platform {host} --json
python "{source / 'plugin/bin/ep_report.py'}" --project "{root}" --output "{root / 'report.md'}"
```

Acceptance observations are local and unsigned. They do not authenticate the
sender, certify a production patch or establish compatibility with other versions.
'''
    if advice:
        instructions += f'''
## Optional advice-delivery observation

This exercise explicitly enables bounded milestone advice (two-second worker,
three attempts, no cooldown). Keep `elevenpowers.milestones.json` unchanged.
After the ordinary source edit, the host callback may supply informational advice.
Run the declared test through the literal wrapper above after that edit, then
inspect readiness from a separate terminal:

```text
python "{source / 'plugin/bin/ep_ready.py'}" {host} --project "{root}" --json
```

Inspect `milestone_advice`: generated context, native emission and subsequent
matching native receipts are separate. A current matching receipt is not proof
of model comprehension, causal advice use or better coding. Preparation and
replay cannot establish installed acceptance. Native matrix captures retain
their base acceptance fields; inspect advice diagnostics separately.
'''
    (root / 'EXERCISE.md').write_text(instructions, encoding='utf-8')
    return {**value, 'project': str(root), 'instructions': str(root / 'EXERCISE.md')}


def _fingerprint(root, name):
    path = root / name
    if path.is_symlink() or path.parent.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError('linked or escaped exercise file')
    with path.open('rb') as stream:
        data = stream.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024:
        raise ValueError('exercise file exceeds read limit')
    return hashlib.sha256(data).hexdigest()


def inspect(host, root, timeout=10):
    """Qualify retained local observations; never launch a host or write state."""
    from .. import health
    from .readiness import identity
    if host not in PATHS:
        raise ValueError('unsupported host')
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 <= timeout <= 120:
        raise ValueError('acceptance seconds must be between 0 and 120')
    started = time.monotonic()
    root = Path(root).resolve(strict=True)
    value = {'schema_version': 1, 'state': 'incomplete', 'host': host, 'project': str(root),
             'host_version': 'unavailable', 'version_source': 'unavailable', 'checks': {},
             'outcomes': {'pass': False, 'fail': False, 'incomplete': False}, 'next_actions': [],
             'limits': ['Local native observations are unsigned; they do not authenticate a host or certify a production patch.',
                        'Acceptance is limited to this exercise, retained history and the recorded operator version.',
                        'Current freshness is checked; the earlier manual stale-view step is not independently attested.']}
    try:
        from .provenance import fingerprint
        runtime_before = fingerprint()
        path = root / '.elevenpowers/acceptance.json'
        manifest = read_json(path)
        if (not isinstance(manifest, dict) or manifest.get('schema_version') != 1 or
                manifest.get('host') != host or manifest.get('state') != 'prepared' or
                manifest.get('language') not in ('python', 'javascript') or
                type(manifest.get('prepared_at')) not in (int, float) or
                not math.isfinite(manifest['prepared_at']) or manifest['prepared_at'] <= 0 or
                manifest.get('version_source') not in ('operator', 'unavailable') or
                not isinstance(manifest.get('host_version'), str) or len(manifest['host_version']) > 128):
            raise ValueError('missing or invalid acceptance manifest')
        files = ('app.py', 'check.py') if manifest['language'] == 'python' else ('app.mjs', 'check.test.mjs')
        if (manifest.get('source_file'), manifest.get('test_file')) != files:
            raise ValueError('exercise paths do not match the language contract')
        if type(manifest.get('advice_requested', False)) is not bool:
            raise ValueError('invalid advice exercise selection')
        if manifest.get('advice_requested') and _fingerprint(root, 'elevenpowers.milestones.json') != manifest.get('milestone_declaration'):
            value['next_actions'].append('Advice milestone declaration changed; prepare a new exercise.')
            raise ValueError('advice declaration changed')
        initial = _fingerprint(root, files[0])
        test = _fingerprint(root, files[1])
        project = _fingerprint(root, '.elevenpowers/config.json')
        native = _fingerprint(root, str(config_path(host, root).relative_to(root)))
        contract_before = (initial, test, project, native)
        checks = value['checks']
        checks.update(test_unchanged=test == manifest.get('test_fingerprint'),
                      runtime_identity=manifest.get('runtime_fingerprint') == runtime_before,
                      project_configuration=project == manifest.get('project_configuration'),
                      native_configuration=native == manifest.get('configuration'),
                      source_changed=initial != manifest.get('initial_source'),
                      host_version=manifest['version_source'] == 'operator' and bool(manifest['host_version']) and
                                   manifest['host_version'] != 'unavailable')
        value.update(language=manifest['language'], host_version=manifest['host_version'],
                     version_source=manifest['version_source'])
        snapshot = health.inspect(host, root, timeout=max(0, timeout - (time.monotonic() - started)))
        if manifest.get('advice_requested'):
            value['milestone_advice'] = snapshot['milestone_advice']
        live = snapshot['activation']
        checks['generation'] = bool(manifest.get('generation')) and live.get('generation') == manifest['generation']
        # The immutable preparation config declares one test command. Exporter
        # commands are portable, so use the project-owned declaration for identity.
        from ..config import load
        checks['command'] = load(root).commands == {'tests': manifest.get('command')}
        startup = live.get('phases', {}).get('SessionStart', {})
        checks['startup_runtime'] = startup.get('runtime_fingerprint') == runtime_before
        value['runtime_fingerprint'] = manifest.get('runtime_fingerprint', '')
        session, task = startup.get('session', ''), identity(snapshot['task'])
        checks['startup_after_preparation'] = bool(session and startup.get('last_at', 0) >= manifest['prepared_at'])
        links = [link for link in live.get('receipt_links', []) if task and session and
                 link['task'] == task and link['session'] == session and link['at'] >= manifest['prepared_at']]
        for link in links:
            outcome = 'incomplete' if link['execution'] == 'incomplete' else link['result']
            if outcome in value['outcomes']:
                value['outcomes'][outcome] = True
        stop = live.get('phases', {}).get('Stop', {})
        checks['completion_after_commands'] = bool(links and stop.get('last_at', 0) >= max(x['at'] for x in links))
        checks['fresh_pipeline'] = snapshot['health']['state'] == 'observed'
        value['health'] = snapshot['health']
        value['task_state'] = snapshot['task_state']
        contract_after = tuple(_fingerprint(root, name) for name in
                               (files[0], files[1], '.elevenpowers/config.json',
                                str(config_path(host, root).relative_to(root))))
        if contract_after != contract_before or activation(host, root) != live:
            value['next_actions'].append('Exercise contract or native observations changed during inspection; read again.')
            raise ValueError('exercise changed during read')
        if fingerprint() != runtime_before or read_json(path) != manifest or time.monotonic() - started >= timeout:
            raise ValueError('exercise changed or acceptance read deadline reached')
        immutable = ('test_unchanged', 'project_configuration', 'native_configuration', 'generation', 'command', 'runtime_identity')
        if not all(checks[k] for k in immutable):
            value['next_actions'].append('Exercise contract, runtime or wiring changed; prepare a new exercise.')
        elif session and not checks['startup_runtime']:
            value['next_actions'].append('Native startup belongs to another or an unbound runtime; start a new exercise/session.')
        elif snapshot['health']['stages']['verification']['state'] == 'failed':
            value['state'] = 'failed'
        elif snapshot['health']['state'] in ('incomplete', 'attention'):
            value['next_actions'].extend(snapshot['next_actions'])
        elif all(checks.values()) and all(value['outcomes'].values()):
            value['state'] = 'passed'
            if manifest.get('advice_requested') and not (
                    snapshot['milestone_advice']['state'] == 'emitted' and
                    any(row['state'] == 'current' for row in snapshot['milestone_advice']['checks'])):
                value['state'] = 'waiting'
                value['next_actions'].append('Optional advice exercise needs a qualified emission and subsequent current native check.')
        else:
            value['state'] = 'incomplete' if live.get('links_evicted') else 'waiting'
            value['next_actions'].extend('Required acceptance observation: ' + k for k, present in
                                         {**checks, **value['outcomes']}.items() if not present)
    except (ValueError, OSError, TypeError, KeyError, AttributeError) as exc:
        value['state'] = 'incomplete'
        value['next_actions'].append('Acceptance diagnostics unavailable: ' + type(exc).__name__)
    value['read_ms'] = round((time.monotonic() - started) * 1000, 3)
    from ..redact import scrub_values
    return scrub_values(value)


def render(value):
    lines = [f"ElevenPowers native acceptance: {value['state']} ({value['host']})",
             f"Project: {value['project']}",
             f"Host version: {value['host_version']} ({value['version_source']})"]
    lines.extend(f"Check {k}: {'observed' if v else 'missing'}" for k, v in value['checks'].items())
    lines.extend(f"Outcome {k}: {'observed' if v else 'missing'}" for k, v in value['outcomes'].items())
    lines.extend('Next action: ' + action for action in value['next_actions'])
    lines.extend('Limit: ' + limit for limit in value['limits'])
    return '\n'.join(lines)
