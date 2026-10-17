"""Human reports share source reads without weakening closing freshness."""
import os

import pytest

from core.config import Config,save
from core.evidence import Evidence,Kind,Result,source_snapshot
from core.ledger import Ledger
from core.obligations import Claim
from core.report import end_report


def seeded(root, *, source=True):
    (root/'value.py').write_text('value = 1\n')
    save(root,Config(profile='guide',auto_detect=False,strength={'enabled':False}))
    scan,tree=source_snapshot(root,fresh=True)
    ledger=Ledger(root=root,task='source-report',claims=[Claim.DOCS_CHANGED])
    ledger.evidence=[Evidence(kind=Kind.SUITE,identity=f'suite-{i}',result=Result.PASS,
        observed=scan.files,tree=tree,scope='source' if source else 'files') for i in range(5)]
    return ledger


def count_scans(monkeypatch):
    from core import evidence
    original=evidence.source_snapshot;calls=[]
    def counted(*args,**kwargs):
        calls.append(kwargs)
        return original(*args,**kwargs)
    monkeypatch.setattr(evidence,'source_snapshot',counted)
    return calls


def test_source_report_uses_only_opening_and_closing_fresh_reads(tmp_path,monkeypatch):
    ledger=seeded(tmp_path);calls=count_scans(monkeypatch)
    text=end_report(ledger)
    assert text.startswith('VERIFIED') and '5 fresh' in text
    assert len(calls)==2,'Repeated per-receipt source scans survived the report boundary'
    assert all(c['fresh'] is True for c in calls)


@pytest.mark.parametrize('move',['bytes','configuration'])
def test_late_movement_cannot_leave_verified_text(tmp_path,monkeypatch,move):
    import core.report as report
    ledger=seeded(tmp_path);original=report._coverage_warnings
    def changing(value):
        result=original(value)
        if move=='bytes':
            path=tmp_path/'value.py';stamp=path.stat()
            path.write_text('value = 2\n');os.utime(path,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
        else:save(tmp_path,Config(profile='off',auto_detect=False))
        return result
    monkeypatch.setattr(report,'_coverage_warnings',changing)
    text=end_report(ledger)
    assert text.startswith('UNVERIFIED'),text
    assert 'during freshness inspection' in text
    assert '5 fresh' not in text


def test_separate_reports_reinspect_current_bytes(tmp_path,monkeypatch):
    ledger=seeded(tmp_path);calls=count_scans(monkeypatch)
    assert '5 fresh' in end_report(ledger)
    (tmp_path/'value.py').write_text('value = 2\n')
    assert '0 fresh' in end_report(ledger)
    assert len(calls)==4


def test_file_scoped_report_does_not_add_full_source_scans(tmp_path,monkeypatch):
    ledger=seeded(tmp_path,source=False);calls=count_scans(monkeypatch)
    end_report(ledger)
    assert calls==[]


def test_incomplete_closing_source_scan_refuses_green_text(tmp_path,monkeypatch):
    import core.evidence as evidence
    ledger=seeded(tmp_path);original=evidence.source_snapshot;calls=[]
    def closing(*args,**kwargs):
        value=original(*args,**kwargs);calls.append(value)
        if len(calls)==2:value[0].issues.append('omitted source input')
        return value
    monkeypatch.setattr(evidence,'source_snapshot',closing)
    text=end_report(ledger)
    assert text.startswith('UNVERIFIED') and '5 fresh' not in text


def test_exhausted_owner_deadline_stays_incomplete(tmp_path):
    from core.jobs import Session
    ledger=seeded(tmp_path)
    with Session(tmp_path,ledger.task,seconds=.0001):text=end_report(ledger)
    assert text.startswith('UNVERIFIED') and 'Incomplete current input inspection' in text
