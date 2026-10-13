"""Actual dependencies can drift without source, HEAD or environment drift."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from core.config import Config, save
from core.ledger import Ledger
from tests.test_patchproof_identity import commit, git


@pytest.fixture(params=['python', 'javascript'])
def dependency_project(tmp_path, request):
    root, dependency = tmp_path/'project', tmp_path/'installed'
    root.mkdir(); dependency.mkdir()
    git(root, 'init', '-q')
    git(root, 'config', 'core.autocrlf', 'false')
    Ledger(root=root).save()
    language = request.param
    if language == 'python':
        target = dependency/'parser.py'
        target.write_text('value=2\n')
        script = root/'check.py'
        script.write_text('from pathlib import Path\nimport runpy\n'
            "p=Path('.elevenpowers/count.txt')\n"
            "p.write_text(str(int(p.read_text())+1) if p.exists() else '1')\n"
            f'assert runpy.run_path({str(target)!r})["value"] == 2\n'
            'print("verified actual dependency behavior")\n')
        args = [sys.executable, '-B', 'check.py']
    else:
        node = shutil.which('node')
        if not node:
            pytest.skip('actual Node producer unavailable')
        target = dependency/'parser.cjs'
        target.write_text('module.exports={value:2};\n')
        script = root/'check.cjs'
        script.write_text("const fs=require('node:fs'),assert=require('node:assert/strict');\n"
            "const p='.elevenpowers/count.txt';\n"
            "fs.writeFileSync(p,String(fs.existsSync(p)?Number(fs.readFileSync(p))+1:1));\n"
            f'assert.equal(require({json.dumps(str(target))}).value,2);\n'
            'console.log("verified actual dependency behavior");\n')
        args = [node, 'check.cjs']
    policy = {'schema': 1, 'witnesses': [{'id': 'dependencies', 'root': 'deps', 'paths': [target.name]}]}
    (root/'elevenpowers.inputs.json').write_text(json.dumps(policy))
    project_identity = hashlib.sha256(str(root.resolve()).encode()).hexdigest()
    (root/'.elevenpowers/input-roots.json').write_text(json.dumps(
        {'schema': 1, 'project': project_identity, 'roots': {'deps': str(dependency.resolve())}}))
    base = commit(root, 'declared independent dependency')
    (root/'service.py').write_text('value=2\n')
    head = commit(root, 'project change')
    command = subprocess.list2cmdline(args)
    save(root, Config(auto_detect=False, commands={'tests': command}))
    return root, base, head, target, language, args


def test_changed_installed_bytes_prevent_obsolete_reuse(dependency_project):
    from core.patchproof.execution import verify
    from core.patchproof.planning import plan
    root, base, head, target, language, args = dependency_project
    first = verify(root, base, head, seconds=120)
    assert first['state'] == 'passed', (first['issues'], first['checks'], first['bundle']['binding'])
    before = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
    environment = dict(os.environ)
    target.write_text('value=9\n' if language == 'python' else 'module.exports={value:9};\n')
    independent = subprocess.run(args, cwd=root, capture_output=True, timeout=20)
    assert independent.returncode != 0, 'independent current behavior must fail'
    assert before == {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
    assert git(root, 'rev-parse', 'HEAD').decode() == head
    assert dict(os.environ) == environment
    planned = plan(root, base, head, seconds=120)
    assert planned['checks'][0]['action'] == 'run', 'unchanged source must not authorize reuse after dependency drift'
    result = verify(root, base, head, seconds=120)
    assert result['state'] == 'failed', result
    assert result['checks'][0]['status'] == 'failed'
    assert (root/'.elevenpowers/count.txt').read_text() == '3'


def test_unchanged_installed_bytes_retain_legitimate_reuse(dependency_project):
    from core.patchproof.execution import verify
    root, base, head, *_ = dependency_project
    first = verify(root, base, head, seconds=120)
    assert first['state'] == 'passed', (first['issues'], first['checks'], first['bundle']['binding'])
    value = verify(root, base, head, seconds=120)
    assert value['state'] == 'passed', value
    assert value['checks'][0]['status'] == 'reused'
    assert (root/'.elevenpowers/count.txt').read_text() == '1'
