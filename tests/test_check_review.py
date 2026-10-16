"""Independent review regressions: obligation state, not declaration-only filters."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from core.config import Config, save
from core.ledger import Ledger
from core.obligations import Obligation
from core.parsers import DECLARED_KINDS, parse

CLI = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_check.py'


@pytest.mark.parametrize('property', ['tests', 'build', 'typecheck', 'lint', 'benchmark'])
def test_outer_success_cannot_satisfy_any_owned_check_obligation(tmp_path, property):
    (tmp_path / 'check.py').write_text('raise SystemExit(1)\n')
    save(tmp_path, Config(profile='guide', commands={property:f'"{sys.executable}" check.py .'}, auto_detect=False))
    Ledger(root=tmp_path,task='review').save()
    inner = f'"{sys.executable}" "{CLI}" {property} --project . --json'
    outer = inner + (' & echo outer-complete' if os.name == 'nt' else '; echo outer-complete')
    done = subprocess.run(outer, cwd=tmp_path, shell=True, capture_output=True, text=True, timeout=30)
    assert done.returncode == 0
    obligation = Obligation(property, DECLARED_KINDS[property], 'the selected check passes', 'run the check')
    ledger = Ledger.load(tmp_path)
    assert obligation.satisfied_by(ledger.evidence) is None
    ledger.add(parse(outer,done.stdout,done.returncode,tmp_path)); ledger.save()
    assert obligation.satisfied_by(Ledger.load(tmp_path).evidence) is None


def test_requested_allowance_above_300_is_not_silently_capped(tmp_path, monkeypatch):
    import core.checks as checks
    save(tmp_path, Config(profile='guide', commands={'build':'real-build-command'}, auto_detect=False))
    observed = []
    def completed(command,root,seconds):
        observed.append(seconds)
        return subprocess.CompletedProcess(command,0,'','')
    monkeypatch.setattr(checks, '_run', completed)
    assert checks.execute(tmp_path, 'build', seconds=600)['state'] == 'passed'
    assert len(observed) == 1 and 300 < observed[0] <= 600


@pytest.mark.skipif(os.name != 'nt', reason='actual Windows encoded invocation producer')
def test_actual_encoded_runner_envelope_does_not_become_a_typecheck(tmp_path):
    from core.checks import guidance
    from core.process import run
    (tmp_path / 'check.py').write_text('raise SystemExit(1)\n')
    save(tmp_path, Config(profile='guide', commands={'typecheck':f'"{sys.executable}" check.py .'}, auto_detect=False))
    command = guidance(tmp_path).removeprefix('Declared-check runner: ') + ' & echo outer-complete'
    started=time.monotonic()
    try:
        done = run(command,cwd=tmp_path,shell=True,timeout=30)
    except subprocess.SubprocessError as error:
        pytest.fail(json.dumps({'state':'incomplete','error':type(error).__name__,
            'seconds':round(time.monotonic()-started,3),
            'stdout':str(getattr(error,'stdout',''))[-4096:],
            'stderr':str(getattr(error,'stderr',''))[-4096:]},indent=2))
    diagnostic={'exit_code':done.returncode,'seconds':round(time.monotonic()-started,3),
                'stdout':done.stdout[-4096:],'stderr':done.stderr[-4096:]}
    assert done.returncode == 0,diagnostic
    assert parse(command,done.stdout,0,tmp_path) == [],diagnostic


def test_unrelated_genuine_typecheck_still_produces_evidence(tmp_path):
    (tmp_path / 'check.py').write_text('raise SystemExit(0)\n')
    command = f'"{sys.executable}" check.py .'
    save(tmp_path,Config(profile='guide',commands={'typecheck':command},auto_detect=False))
    done = subprocess.run(command,cwd=tmp_path,shell=True,capture_output=True,text=True,timeout=15)
    records = parse(command,done.stdout,done.returncode,tmp_path)
    from core.evidence import Kind
    obligation = Obligation('typecheck',Kind.TYPECHECK,'type check passes','run it')
    assert obligation.satisfied_by(records) is not None
