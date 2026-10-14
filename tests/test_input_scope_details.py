"""Unknown scope state and per-witness expiry must stay distinguishable."""
import json

from core.inputs.receipts import inspect
from tests.test_input_scopes import scoped_project, observed_run
from tests.test_external_input_reuse import dependency_project


def test_structurally_unknown_scope_is_incomplete_not_known_changed(scoped_project):
    root,target,other,commands,*_=scoped_project
    _,records=observed_run(root,commands[1])
    (root/'elevenpowers.inputs.json').write_text('{"schema":2,"witnesses":')
    assert inspect(records[-1],root)['state']=='incomplete'


def test_report_names_changed_witness_within_multi_input_scope(scoped_project):
    root,target,other,commands,args,policy=scoped_project
    policy['commands'][1]['witnesses']=['first','second']
    (root/'elevenpowers.inputs.json').write_text(json.dumps(policy))
    _,records=observed_run(root,commands[1])
    target.write_text('value=9\n' if target.suffix=='.py' else 'module.exports={value:9};\n')
    result=inspect(records[-1],root)
    assert result['state']=='stale'
    assert result['changed_witnesses']==['first']


def test_redacted_declared_identity_cannot_license_narrowing(scoped_project):
    from core.inputs.collection import capture
    from core.config import Config, save
    import time
    root,target,other,commands,args,policy=scoped_project
    commands=[commands[0]+' token=fixture-first1',commands[0]+' token=fixture-second2']
    from core.redact import scrub
    assert scrub(commands[0])==scrub(commands[1]),'actual public identities must collide in this control'
    save(root,Config(auto_detect=False,commands={'tests':commands[0],'build':commands[1]}))
    for row,command in zip(policy['commands'],commands): row['command']=command
    (root/'elevenpowers.inputs.json').write_text(json.dumps(policy))
    code,records=observed_run(root,commands[1])
    assert code==0
    assert capture(root,time.monotonic()+10)['state']=='incomplete'
    assert inspect(records[-1],root)['state']=='incomplete'


def test_unobserved_after_is_unknown_not_a_witness_change(scoped_project):
    from core.inputs.native import before
    from core.ledger import Ledger
    from tests.test_input_native import event
    root,target,other,commands,*_=scoped_project
    ledger=Ledger.load(root);ledger.task='unfinished scoped execution';ledger.save()
    assert before(event(root,commands[0],call='unfinished'),root)
    provisional=Ledger.load(root).evidence[-1]
    result=inspect(provisional,root)
    assert result['state']=='incomplete'
    assert result['changed_witnesses']==[]


def test_markdown_explains_the_changed_input_scope(scoped_project):
    from core.export import build, markdown
    from core.ledger import Ledger
    root,target,other,commands,args,policy=scoped_project
    policy['commands'][1]['witnesses']=['first','second']
    (root/'elevenpowers.inputs.json').write_text(json.dumps(policy))
    _,records=observed_run(root,commands[1])
    ledger=Ledger.load(root);ledger.add(records);ledger.save()
    target.write_text('value=9\n' if target.suffix=='.py' else 'module.exports={value:9};\n')
    text=markdown(build(root,timeout=120))
    assert 'Selected witnesses: first, second' in text
    assert 'Changed selected witnesses: first' in text
    assert str(target.parent) not in text


def test_unapproved_other_root_does_not_disqualify_approved_scope(scoped_project):
    root,target,other,commands,args,policy=scoped_project
    policy['witnesses'][0]['root']='unapproved'
    (root/'elevenpowers.inputs.json').write_text(json.dumps(policy))
    code,records=observed_run(root,commands[1])
    assert code==0
    assert inspect(records[-1],root)['state']=='bound'
