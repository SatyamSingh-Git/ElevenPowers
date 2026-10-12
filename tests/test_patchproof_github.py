"""Read-only GitHub subjects preserve real PatchProof qualifications."""
import json
from pathlib import Path
import shutil

import pytest

from core.config import Config, save
from core.evidence import Result
from tests.test_patchproof_report import project, seed
from tests.test_patchproof_identity import commit


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def event(base, head, repo='example/project'):
    return {'number': 7, 'pull_request': {'base': {'sha': base, 'repo': {'full_name': repo}},
            'head': {'sha': head, 'repo': {'full_name': 'contributor/fork'}}}}


@pytest.mark.parametrize(('result', 'execution', 'expected'), [
    (Result.PASS, 'complete', 'current'), (Result.FAIL, 'complete', 'failed'),
    (Result.PASS, 'incomplete', 'incomplete')])
def test_presentation_retains_check_outcomes_without_executing(project, result, execution, expected):
    from core.patchproof.github import build
    root, base, head = project
    seed(root, result=result, execution=execution, declaration='tests')
    save(root, Config(auto_detect=False, commands={'tests': 'python -m pytest', 'typecheck': 'never-run'}))
    before = snapshot(root)
    value = build(root, base, head, repository='example/project', event=event(base, head))
    assert snapshot(root) == before
    assert value['kind'] == 'patchproof_github' and value['schema_version'] == 1
    assert value['subject']['head_repository'] == 'contributor/fork'
    assert value['subject']['state'] == 'matched_event'
    assert [c['state'] for c in value['bundle']['checks']] == [expected, 'absent']
    assert value['bundle']['verification']['state'] == 'UNVERIFIED'
    assert value['meaning'] == 'informational evidence export, not patch safety'
    assert len(value['bundle_sha256']) == 64
    assert 'private prompt' not in json.dumps(value)
    assert 'private receipt detail' not in json.dumps(value)


def test_dirty_and_stale_inputs_remain_unavailable(project):
    from core.patchproof.github import build
    root, base, head = project
    seed(root, declaration='tests')
    save(root, Config(auto_detect=False, commands={'tests': 'python -m pytest'}))
    (root / 'service.py').write_text('value=999\n')
    value = build(root, base, head, repository='another/service')
    assert value['subject']['state'] == 'declared'
    assert value['bundle']['binding']['state'] == 'unavailable'
    assert value['bundle']['checks'][0]['state'] == 'stale'
    assert value['bundle']['receipts'][0]['association'] == 'unavailable'


@pytest.mark.parametrize('wrong', ['repository', 'head', 'base'])
def test_wrong_pr_subject_refuses_presentation(project, wrong):
    from core.patchproof.github import build
    root, base, head = project
    context = event(base, head)
    if wrong == 'repository':
        context['pull_request']['base']['repo']['full_name'] = 'elsewhere/repo'
    elif wrong == 'head':
        (root / 'merge.py').write_text('merged=True\n')
        head = commit(root, 'synthetic merge')
    else:
        context['pull_request']['base']['sha'] = 'a' * 40
    with pytest.raises(ValueError):
        build(root, base, head, repository='example/project', event=context)


def test_event_reader_refuses_duplicate_nonfinite_and_excessive_inputs(tmp_path):
    from core.patchproof.github_context import read_event, MAX_EVENT_BYTES
    path = tmp_path / 'event.json'
    for text in ('{"number":1,"number":2}', '{"number":NaN}', '[' * 1500 + '0' + ']' * 1500):
        path.write_text(text)
        with pytest.raises(ValueError):
            read_event(path)
    path.write_bytes(b'x' * (MAX_EVENT_BYTES + 1))
    with pytest.raises(ValueError):
        read_event(path)


@pytest.mark.parametrize('repository', ['https://github.com/a/b', 'a/b/c', '../repo', 'a/..', 'a/b\n::error::oops'])
def test_repository_is_data_with_no_shell_or_url_fallback(project, repository):
    from core.patchproof.github import build
    root, base, head = project
    with pytest.raises(ValueError):
        build(root, base, head, repository=repository)


def test_missing_patch_is_visible_without_inventing_identity(project):
    from core.patchproof.github import build
    root, _, _ = project
    value = build(root, 'missing-ref', 'HEAD', repository='example/project')
    assert value['subject']['state'] == 'unavailable'
    assert value['bundle']['binding']['state'] == 'unavailable'


def test_actual_node_assertion_receipt_is_presented_without_rerun(project):
    from core.patchproof.github import build
    from core.ledger import Ledger
    from core.parsers import parse
    from core.process import run
    node = shutil.which('node')
    if not node:
        pytest.skip('Node producer unavailable')
    root, base, _ = project
    Ledger(root=root).save()
    (root / 'service.cjs').write_text('exports.value=2;\n')
    (root / 'check.cjs').write_text(
        "const test=require('node:test'),assert=require('node:assert/strict');\n"
        "test('independent expected value',()=>assert.equal(require('./service.cjs').value,2));\n")
    head = commit(root, 'Node assertion')
    command = f'"{node}" --test check.cjs'
    save(root, Config(auto_detect=False, commands={'tests': command}))
    done = run(command, cwd=root, timeout=10)
    assert done.returncode == 0
    ledger = Ledger.load(root)
    ledger.add(parse(command, done.stdout + done.stderr, done.returncode, root))
    ledger.save()
    before = snapshot(root)
    value = build(root, base, head, repository='another/node-project')
    assert snapshot(root) == before
    assert value['bundle']['checks'][0]['state'] == 'current'
    assert any(r['passed'] == 1 for r in value['bundle']['receipts'])
