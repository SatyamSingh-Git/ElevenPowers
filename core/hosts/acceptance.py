"""Explicit disposable native exercises; preparation is never live acceptance."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
import uuid

from ..config import Config, save
from ..process import run
from .readiness import activation, signature
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


def prepare(host, destination, language, source, version=''):
    if host not in PATHS:
        raise ValueError('unsupported host')
    if language not in ('python', 'javascript'):
        raise ValueError('unsupported acceptance language')
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
    root.mkdir()
    app, test = ('app.py', 'check.py') if language == 'python' else ('app.mjs', 'check.test.mjs')
    (root / app).write_text(PYTHON_SOURCE if language == 'python' else JS_SOURCE, encoding='utf-8')
    (root / test).write_text(PYTHON_TEST if language == 'python' else JS_TEST, encoding='utf-8')
    (root / '.gitignore').write_text('.elevenpowers/\nwait.flag\n__pycache__/\n', encoding='utf-8')
    command = f'"{runtime}" ' + ('check.py' if language == 'python' else '--test check.test.mjs')
    save(root, Config(profile='guide', commands={'tests': command}, auto_detect=False, strength={'enabled': False}))
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
             'version_source': 'operator' if version else 'unavailable',
             'generation': activation(host, root)['generation'],
             'configuration': signature(config_path(host, root)),
             'project_configuration': signature(root / '.elevenpowers/config.json'),
             'initial_source': signature(root / app), 'test_fingerprint': signature(root / test)}
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
    (root / 'EXERCISE.md').write_text(instructions, encoding='utf-8')
    return {**value, 'project': str(root), 'instructions': str(root / 'EXERCISE.md')}
