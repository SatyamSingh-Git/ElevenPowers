"""Required external observations qualify execution, not source-only claims."""
import json
from pathlib import Path

import pytest

from tests.test_external_input_reuse import dependency_project
from tests.test_patchproof_identity import commit


def test_missing_approval_blocks_first_execution_without_counter_write(dependency_project):
    from core.patchproof.execution import verify
    root,base,head,*_ = dependency_project
    (root/'.elevenpowers/input-roots.json').unlink()
    result = verify(root,base,head,seconds=120)
    assert result['state'] == 'incomplete'
    assert all(c['status']=='deferred' for c in result['checks'])
    assert not (root/'.elevenpowers/count.txt').exists()
    assert result['bundle']['external_inputs']['state'] == 'incomplete'


def test_drift_during_actual_command_is_stale_and_preserved(dependency_project):
    from core.patchproof.execution import verify
    from core.patchproof.execution_state import read
    root,base,_,target,language,_ = dependency_project
    script = root/('check.py' if language=='python' else 'check.cjs')
    if language == 'python':
        with script.open('a') as stream:
            stream.write(f'Path({str(target)!r}).write_bytes(b"value=9\\n")\n')
    else:
        with script.open('a') as stream:
            stream.write(f'fs.writeFileSync({json.dumps(str(target))},"module.exports={{value:9}};\\n");\n')
    head = commit(root,'actual dependency mutation during check')
    result = verify(root,base,head,seconds=120)
    assert result['state'] == 'incomplete'
    assert result['checks'][0]['status'] == 'stale'
    saved = read(root)['attempts'][-1]
    assert saved['exit_code'] == 0 and saved['status'] == 'stale'
    assert saved['witness'] != saved['after']


def test_legacy_history_cannot_invent_new_external_association(dependency_project):
    from core.patchproof.execution import verify
    from core.patchproof.execution_state import read,save
    from core.patchproof.planning import plan
    root,base,head,*_ = dependency_project
    assert verify(root,base,head,seconds=120)['state'] == 'passed'
    saved = read(root)
    for item in saved['attempts']:
        item['witness'].pop('external_inputs_fingerprint',None)
        item['after'].pop('external_inputs_fingerprint',None)
    save(root,saved)
    old_bytes = (root/'.elevenpowers/patch-verification.json').read_bytes()
    result = plan(root,base,head,seconds=120)
    assert result['ready'] and result['checks'][0]['action'] == 'run'
    assert (root/'.elevenpowers/patch-verification.json').read_bytes() == old_bytes
    assert (root/'.elevenpowers/count.txt').read_text() == '1'


def test_report_preserves_source_facts_but_explains_external_drift(dependency_project):
    from core.patchproof.execution import verify
    from core.patchproof.report import build,markdown
    from core.patchproof.github import build as github
    from core.patchproof.github_output import markdown as github_markdown
    from tests.test_input_collection import snapshot
    root,base,head,target,language,_ = dependency_project
    assert verify(root,base,head,seconds=120)['state'] == 'passed'
    current = build(root,base,head)
    assert current['execution']['checks'][0]['external_inputs_association'] == 'bound'
    target.write_text('value=9\n' if language=='python' else 'module.exports={value:9};\n')
    before = snapshot(root)
    changed = build(root,base,head)
    assert changed['binding']['state'] == 'bound'
    assert changed['checks'][0]['state'] == 'current', 'source-only receipt facts remain unchanged'
    assert changed['execution']['checks'][0]['association'] == 'unavailable'
    assert changed['execution']['checks'][0]['external_inputs_association'] == 'unavailable'
    assert changed['external_inputs']['state'] == 'available'
    assert 'Declared external inputs' in markdown(changed)
    presented = github(root,base,head,repository='example/project')
    assert 'Declared external inputs' in github_markdown(presented)
    assert str(target.parent) not in json.dumps(presented)
    assert snapshot(root) == before and (root/'.elevenpowers/count.txt').read_text() == '1'


def test_unconfigured_report_does_not_inspect_unused_approval(tmp_path):
    from tests.test_patchproof_report import seed
    from tests.test_patchproof_identity import git
    from core.patchproof.report import build
    git(tmp_path,'init','-q')
    (tmp_path/'service.py').write_bytes(b'value=1\n')
    base = commit(tmp_path,'base')
    (tmp_path/'service.py').write_bytes(b'value=2\n')
    head = commit(tmp_path,'change')
    seed(tmp_path)
    outside = tmp_path/'unrelated'; outside.write_bytes(b'unrelated private data')
    # Keep unrelated content ignored, not an untracked patch input.
    outside.unlink()
    unused = tmp_path/'.elevenpowers/unused.json'; unused.write_bytes(b'unrelated private data')
    try:
        (tmp_path/'.elevenpowers/input-roots.json').symlink_to(unused)
    except OSError:
        pytest.skip('symlinks unavailable')
    value = build(tmp_path,base,head)
    assert value['external_inputs']['state'] == 'not_configured'
    assert value['binding']['state'] == 'bound', value['binding']['issues']
