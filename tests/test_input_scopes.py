"""Independent external consumers must not share unrelated invalidation."""
import json
import subprocess
import time

import pytest

from core.config import Config, save
from core.evidence import Freshness
from core.inputs.collection import capture
from core.inputs.receipts import attach, inspect
from core.parsers import parse
from tests.test_external_input_reuse import dependency_project


@pytest.fixture
def scoped_project(dependency_project):
    root, base, head, target, language, args = dependency_project
    other = target.with_name('other' + target.suffix)
    other.write_bytes(target.read_bytes())
    script = root/args[-1]
    second = script.with_name('other' + script.suffix)
    second.write_text(script.read_text().replace(repr(str(target)), repr(str(other)))
        .replace(json.dumps(str(target)), json.dumps(str(other))).replace('count.txt', 'other-count.txt'))
    commands = [subprocess.list2cmdline(args), subprocess.list2cmdline([*args[:-1], second.name])]
    save(root, Config(auto_detect=False, commands={'tests': commands[0], 'build': commands[1]}))
    policy = {'schema': 2, 'witnesses': [
        {'id': 'first', 'root': 'deps', 'paths': [target.name]},
        {'id': 'second', 'root': 'deps', 'paths': [other.name]}], 'commands': [
        {'command': commands[0], 'witnesses': ['first'], 'complete': True},
        {'command': commands[1], 'witnesses': ['second'], 'complete': True}]}
    (root/'elevenpowers.inputs.json').write_text(json.dumps(policy))
    return root, target, other, commands, args, policy


def observed_run(root, command):
    before = capture(root, time.monotonic()+10)
    done = subprocess.run(command, shell=True, cwd=root, capture_output=True, text=True, timeout=20)
    records = parse(command, done.stdout+done.stderr, done.returncode, root)
    after = capture(root, time.monotonic()+10)
    attach(records, before, after, 'a'*64)
    return done.returncode, records


def test_actual_unrelated_drift_retains_only_independent_scope(scoped_project):
    root, target, other, commands, args, _ = scoped_project
    first_code, first = observed_run(root, commands[0])
    second_code, second = observed_run(root, commands[1])
    assert (first_code, second_code) == (0, 0)
    assert inspect(first[-1], root)['state'] == inspect(second[-1], root)['state'] == 'bound'
    target.write_text('value=9\n' if target.suffix=='.py' else 'module.exports={value:9};\n')
    assert subprocess.run(args, cwd=root, capture_output=True, timeout=20).returncode != 0
    assert inspect(first[-1], root)['state'] == 'stale'
    assert inspect(second[-1], root)['state'] == 'bound'
    assert first[-1].source_freshness(root) is second[-1].source_freshness(root) is Freshness.FRESH


def test_missing_unrelated_witness_does_not_hide_valid_scope(scoped_project):
    root, target, other, commands, *_ = scoped_project
    _, first = observed_run(root, commands[0])
    _, second = observed_run(root, commands[1])
    target.unlink()
    assert inspect(first[-1], root)['state'] == 'incomplete'
    assert inspect(second[-1], root)['state'] == 'bound'


def test_partial_scope_keeps_broad_fallback(scoped_project):
    root, target, other, commands, args, policy = scoped_project
    policy['commands'][1]['complete'] = False
    (root/'elevenpowers.inputs.json').write_text(json.dumps(policy))
    _, second = observed_run(root, commands[1])
    assert inspect(second[-1], root)['state'] == 'bound'
    target.write_text('value=9\n' if target.suffix=='.py' else 'module.exports={value:9};\n')
    assert inspect(second[-1], root)['state'] == 'stale'


def test_native_paired_scope_survives_other_input_drift(scoped_project):
    from core.inputs.native import before, after
    from core.ledger import Ledger
    from tests.test_input_native import event
    root, target, other, commands, *_ = scoped_project
    ledger=Ledger.load(root);ledger.task='scoped native exercise';ledger.save()
    payload=event(root,commands[1],call='scoped')
    assert before(payload,root)
    done=subprocess.run(commands[1],shell=True,cwd=root,capture_output=True,text=True,timeout=20)
    assert done.returncode==0
    records=parse(commands[1],done.stdout+done.stderr,done.returncode,root)
    assert after(payload,root,records)
    assert inspect(records[-1],root)['state']=='bound'
    target.write_text('value=9\n' if target.suffix=='.py' else 'module.exports={value:9};\n')
    assert inspect(records[-1],root)['state']=='bound'


def test_owned_scope_can_run_when_other_selected_file_missing(scoped_project):
    from core.inputs.execution import begin, ready, finish
    root, target, other, commands, *_ = scoped_project
    target.unlink()
    value=begin(root,time.monotonic()+10,command=commands[1],declared=True)
    assert ready(value)
    done=subprocess.run(commands[1],shell=True,cwd=root,capture_output=True,text=True,timeout=20)
    assert done.returncode==0
    records=parse(commands[1],done.stdout+done.stderr,done.returncode,root)
    finish(root,time.monotonic()+10,value,records)
    assert inspect(records[-1],root)['state']=='bound'


@pytest.mark.parametrize('change', ['empty','unknown','duplicate','boolean','ambiguous'])
def test_invalid_scope_cannot_narrow_coverage(scoped_project,change):
    root, target, other, commands, args, policy=scoped_project
    row=policy['commands'][0]
    if change=='empty': row['witnesses']=[]
    elif change=='unknown': row['witnesses']=['absent']
    elif change=='duplicate': row['witnesses']=['first','first']
    elif change=='boolean': row['complete']=1
    else: policy['commands'].append(dict(row))
    (root/'elevenpowers.inputs.json').write_text(json.dumps(policy))
    assert capture(root,time.monotonic()+10)['state']=='incomplete'


def test_explicit_patch_reuses_only_independent_command(scoped_project):
    from core.patchproof.execution import verify
    from core.patchproof.planning import plan
    from tests.test_patchproof_identity import commit
    root,target,other,commands,args,_=scoped_project
    base=commit(root,'independent command scopes')
    (root/'service.py').write_text('value=3\n')
    head=commit(root,'service change')
    first=verify(root,base,head,seconds=120)
    assert first['state']=='passed',first['issues']
    assert (root/'.elevenpowers/count.txt').read_text()=='1'
    assert (root/'.elevenpowers/other-count.txt').read_text()=='1'
    target.write_text('value=9\n' if target.suffix=='.py' else 'module.exports={value:9};\n')
    choices=plan(root,base,head,seconds=120)
    actions={c['properties'][0]:c['action'] for c in choices['checks']}
    assert actions=={'tests':'run','build':'reuse'},choices['bundle']['execution']
    final=verify(root,base,head,seconds=120)
    assert final['state']=='failed',final['issues']
    assert (root/'.elevenpowers/count.txt').read_text()=='2'
    assert (root/'.elevenpowers/other-count.txt').read_text()=='1'


def test_legacy_broad_receipt_is_not_retroactively_narrowed(scoped_project):
    from core.inputs.receipts import metadata
    root,target,other,commands,*_=scoped_project
    before=capture(root,time.monotonic()+10)
    _,records=observed_run(root,commands[1])
    records[-1].external_inputs=metadata(before,before,'a'*64)
    assert inspect(records[-1],root)['state']=='bound'
    target.write_text('value=9\n' if target.suffix=='.py' else 'module.exports={value:9};\n')
    assert inspect(records[-1],root)['state']=='stale'


def test_scope_removal_cannot_relabel_old_execution(scoped_project):
    root,target,other,commands,args,policy=scoped_project
    _,records=observed_run(root,commands[1])
    policy['commands'][1]['witnesses']=['first']
    (root/'elevenpowers.inputs.json').write_text(json.dumps(policy))
    assert inspect(records[-1],root)['state']=='stale'


def test_missing_unrelated_approved_directory_preserves_available_scope(scoped_project):
    root,target,other,commands,args,policy=scoped_project
    separate=target.parent/'separate';separate.mkdir()
    moved=separate/target.name;moved.write_bytes(target.read_bytes())
    policy['witnesses'][0]['root']='otherroot'
    (root/'elevenpowers.inputs.json').write_text(json.dumps(policy))
    path=root/'.elevenpowers/input-roots.json'
    approval=json.loads(path.read_text());approval['roots']['otherroot']=str(separate.resolve())
    path.write_text(json.dumps(approval))
    _,records=observed_run(root,commands[1])
    assert inspect(records[-1],root)['state']=='bound'
    moved.unlink();separate.rmdir()
    assert inspect(records[-1],root)['state']=='bound'


def test_supported_literal_wrapper_uses_declared_scope(scoped_project):
    root,target,other,commands,*_=scoped_project
    _,records=observed_run(root,f'cd "{root}" && {commands[1]}')
    assert inspect(records[-1],root)['state']=='bound'


    assert records[-1].external_inputs['schema']==2
    target.unlink()
    assert inspect(records[-1],root)['state']=='bound'


