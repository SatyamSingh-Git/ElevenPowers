"""Owned commands must carry actual external observations, including refusals."""
import subprocess

import pytest

from core.evidence import Freshness, Result
from core.inputs.receipts import inspect
from core.ledger import Ledger
from core.obligations import Claim
from tests.test_external_input_reuse import dependency_project


def owned(fixture):
    root,*_=fixture
    ledger=Ledger.load(root)
    ledger.task='owned';ledger.claims=[Claim.REFACTOR_SAFE]
    ledger.save()
    return ledger


def test_owned_receipt_and_reuse_expire_on_external_drift(dependency_project):
    from core.verify import discharge,dischargeable
    root,_,_,target,language,args=dependency_project
    ledger=owned(dependency_project)
    records=discharge(ledger)
    assert records and records[-1].result is Result.PASS
    assert inspect(records[-1],root)['state']=='bound'
    assert dischargeable(ledger)==[]
    assert not discharge(ledger)
    assert (root/'.elevenpowers/count.txt').read_text()=='1'
    target.write_bytes(b'value=9\n' if language=='python' else b'module.exports={value:9};\n')
    assert subprocess.run(args,cwd=root,capture_output=True,timeout=20).returncode==1
    assert inspect(records[-1],root)['state']=='stale'
    assert dischargeable(ledger)==['tests']
    failed=discharge(ledger)
    assert failed[-1].result is Result.FAIL
    assert inspect(failed[-1],root)['state']=='bound'


def test_missing_required_input_refuses_owned_launch(dependency_project):
    from core.verify import discharge
    root,_,_,target,*_=dependency_project
    ledger=owned(dependency_project);target.unlink()
    records=discharge(ledger)
    assert records and records[-1].execution=='incomplete'
    assert not (root/'.elevenpowers/count.txt').exists(), 'must refuse before command startup'
    assert inspect(records[-1],root)['state']=='incomplete'


def test_inputs_changed_by_actual_command_do_not_qualify_pass(dependency_project):
    from core.verify import discharge
    root,_,_,target,language,*_=dependency_project
    script=root/('check.py' if language=='python' else 'check.cjs')
    with script.open('a') as stream:
        if language=='python': stream.write(f'Path({str(target)!r}).write_text("value=9\\n")\n')
        else:
            import json
            stream.write(f'fs.writeFileSync({json.dumps(str(target))},"module.exports={{value:9}};\\n");\n')
    ledger=owned(dependency_project)
    records=discharge(ledger)
    assert records[-1].result is Result.PASS
    assert records[-1].source_freshness(root) is Freshness.FRESH
    assert inspect(records[-1],root)['state']=='stale'


def test_baseline_cache_stamp_tracks_external_bytes(dependency_project):
    from core.stress import _inputs_stamp
    root,base,_,target,*_=dependency_project
    command=Ledger.load(root).config.commands['tests']
    before=_inputs_stamp(root,base,command,())
    assert before and before==_inputs_stamp(root,base,command,())
    target.write_bytes(b'changed actual input\n')
    assert before!=_inputs_stamp(root,base,command,())
    target.unlink()
    assert not _inputs_stamp(root,base,command,()), 'an incomplete capture cannot be a reusable cache identity'


def test_explicit_patchproof_receipts_share_external_metadata(dependency_project):
    from core.patchproof.execution import verify
    root,base,head,*_=dependency_project
    value=verify(root,base,head,seconds=120)
    records=Ledger.load(root).evidence
    assert value['state']=='passed', value['issues']
    assert records and inspect(records[-1],root)['state']=='bound'


@pytest.mark.parametrize('missing',[False,True])
def test_confirmation_reuse_and_launch_require_external_inputs(dependency_project,missing):
    import sys
    from core import stress
    from core.config import Config,save
    root,_,_,target,language,args=dependency_project
    (root/'tests').mkdir()
    (root/'tests/test_dependency.py').write_text('import subprocess\n'
        f'def test_dependency():\n    assert subprocess.run({args!r},capture_output=True).returncode == 0\n')
    command=f'"{sys.executable}" -m pytest -q'
    save(root,Config(auto_detect=False,commands={'tests':command}))
    ledger=owned(dependency_project)
    ledger.failed_before=['tests/test_dependency.py::test_dependency'];ledger.save()
    if missing:
        target.unlink()
        assert not stress.confirm(ledger)
        assert not (root/'.elevenpowers/count.txt').exists()
        assert inspect(ledger.evidence[-1],root)['state']=='incomplete'
        return
    records=stress.confirm(ledger)
    assert records and inspect(records[-1],root)['state']=='bound'
    assert not stress.confirm(ledger)
    assert (root/'.elevenpowers/count.txt').read_text()=='1'
    target.write_bytes(b'value=9\n' if language=='python' else b'module.exports={value:9};\n')
    assert not stress.confirm(ledger)
    assert (root/'.elevenpowers/count.txt').read_text()=='2'
    assert ledger.evidence[-1].result is Result.FAIL
    assert inspect(ledger.evidence[-1],root)['state']=='bound'


def test_unconfigured_owned_interruption_keeps_legacy_serialization(dependency_project,monkeypatch):
    from core import verify
    root,*_=dependency_project
    (root/'elevenpowers.inputs.json').unlink()
    ledger=owned(dependency_project)
    def interrupted(*args,**kwargs): raise KeyboardInterrupt()
    monkeypatch.setattr(verify,'run_command',interrupted)
    with pytest.raises(KeyboardInterrupt): verify.discharge(ledger)
    records=Ledger.load(root).evidence
    assert records and records[-1].execution=='incomplete'
    assert records[-1].external_inputs=={}
    assert 'external_inputs' not in records[-1].to_dict()


def test_confirmation_rechecks_inputs_before_suppressing_execution(dependency_project,monkeypatch):
    import sys
    from core import stress
    from core.config import Config,save
    from core.inputs import execution
    root,_,_,target,language,args=dependency_project
    (root/'tests').mkdir()
    (root/'tests/test_dependency.py').write_text('import subprocess\n'
        f'def test_dependency():\n    assert subprocess.run({args!r},capture_output=True).returncode == 0\n')
    save(root,Config(auto_detect=False,commands={'tests':f'"{sys.executable}" -m pytest -q'}))
    ledger=owned(dependency_project);ledger.failed_before=['tests/test_dependency.py::test_dependency'];ledger.save()
    assert stress.confirm(ledger)
    original=execution.begin
    def moved(root,deadline,**kwargs):
        value=original(root,deadline,**kwargs)
        target.write_bytes(b'value=9\n' if language=='python' else b'module.exports={value:9};\n')
        return value
    monkeypatch.setattr(execution,'begin',moved)
    assert not stress.confirm(ledger)
    assert (root/'.elevenpowers/count.txt').read_text()=='2','a moved collection must not suppress the current failing confirmation'
