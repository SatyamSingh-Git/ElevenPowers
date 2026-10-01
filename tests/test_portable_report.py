import json
import os
import time
from pathlib import Path
import subprocess
import sys

import pytest

from core.evidence import Evidence, Kind, Result, source_snapshot
from core.ledger import Ledger
from core.obligations import Claim


def seeded(root, **extra):
    (root / 'service.py').write_text('value = 1\n')
    scan, tree = source_snapshot(root, fresh=True)
    record = Evidence(kind=Kind.SUITE, identity='suite', result=Result.PASS,
                      observed=scan.files, tree=tree, scope='source', command='python -m pytest', **extra)
    ledger = Ledger(root=root, task='task-1', request='private request text', claims=[Claim.DOCS_CHANGED])
    ledger.evidence = [record]
    ledger.save()
    return ledger


def test_report_records_current_freshness_and_becomes_stale_after_edit(tmp_path):
    from core.export import build
    seeded(tmp_path)
    before = build(tmp_path)
    assert before['schema_version'] == 1
    assert before['receipts'][0]['freshness'] == 'fresh'
    (tmp_path / 'service.py').write_text('value = 2\n')
    after = build(tmp_path)
    assert after['receipts'][0]['freshness'] == 'stale'


def test_empty_project_does_not_claim_verified_work(tmp_path):
    from core.export import build
    value = build(tmp_path)
    assert value['state'] == 'UNVERIFIED'
    assert any('claim' in action for action in value['next_actions'])
    assert not (tmp_path / '.elevenpowers').exists()


def test_incomplete_command_is_not_a_passing_receipt(tmp_path):
    from core.export import build
    seeded(tmp_path, execution='incomplete')
    value = build(tmp_path)
    assert value['receipts'][0]['execution'] == 'incomplete'
    assert any('incomplete' in action for action in value['next_actions'])


def test_one_fresh_source_snapshot_is_shared_with_verdicts(tmp_path, monkeypatch):
    from core import evidence
    from core.export import build
    ledger = seeded(tmp_path)
    ledger.evidence += [Evidence(kind=Kind.SUITE, identity='other suite', result=Result.PASS,
                                observed=ledger.evidence[0].observed, tree=ledger.evidence[0].tree, scope='source')]
    ledger.save()
    original = evidence.source_snapshot
    calls = []
    def counting(*args, **kwargs):
        calls.append(kwargs)
        return original(*args, **kwargs)
    monkeypatch.setattr(evidence, 'source_snapshot', counting)
    build(tmp_path)
    assert len(calls) == 1
    assert calls[0]['fresh'] is True


def test_report_excludes_session_text_scrubs_secrets_and_project_root(tmp_path):
    from core.export import build, markdown
    ledger = seeded(tmp_path, detail='private captured detail')
    token = 'ghp_' + 'A' * 30
    ledger.evidence[0].command = f'check --token={token} "{tmp_path}/service.py"'
    ledger.saw_output('check', 'private captured output')
    ledger.save()
    value = build(tmp_path)
    text = json.dumps(value) + markdown(value)
    assert token not in text
    assert 'private captured' not in text
    assert 'private request text' not in text
    assert str(tmp_path) not in text


def test_markdown_escapes_supplied_text(tmp_path):
    from core.export import build, markdown
    ledger = seeded(tmp_path)
    ledger.evidence[0].command = '<script>alert(1)</script> | `unsafe`\nnext'
    ledger.save()
    text = markdown(build(tmp_path))
    assert '<script>' not in text
    assert '\\|' in text


def test_source_budget_exhaustion_cannot_certify_report(tmp_path):
    from core.export import build
    seeded(tmp_path)
    value = build(tmp_path, timeout=0)
    assert not value['coverage']['complete']
    assert value['state'] == 'UNVERIFIED'


def test_report_is_read_only_and_atomic_writer_preserves_existing_output(tmp_path):
    from core.export import build, write
    seeded(tmp_path)
    ledger_path = tmp_path / '.elevenpowers/ledger.json'
    before = ledger_path.read_bytes()
    build(tmp_path)
    assert ledger_path.read_bytes() == before
    target = tmp_path / 'report.json'
    write(target, 'first')
    with pytest.raises(FileExistsError):
        write(target, 'second')
    assert target.read_text() == 'first'
    write(target, 'second', force=True)
    assert target.read_text() == 'second'


def test_cli_exports_json_from_any_directory(tmp_path):
    from core.export import build
    seeded(tmp_path)
    script = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_report.py'
    done = subprocess.run([sys.executable, str(script), '--project', str(tmp_path), '--format', 'json'],
                          cwd=tmp_path, text=True, capture_output=True, timeout=20)
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout)['schema_version'] == 1


def test_snapshot_view_cannot_leak_between_projects_or_after_export(tmp_path):
    from core.evidence import freshness_view, Freshness
    from core.export import build
    first, second = tmp_path / 'first', tmp_path / 'second'
    first.mkdir()
    second.mkdir()
    one, two = seeded(first), seeded(second)
    (second / 'service.py').write_text('value = 2\n')
    with freshness_view(first):
        assert two.evidence[0].freshness(second) == Freshness.STALE
    build(first)
    (first / 'service.py').write_text('value = 2\n')
    assert one.evidence[0].freshness(first) == Freshness.STALE


def test_omitted_receipts_make_report_incomplete(tmp_path, monkeypatch):
    from core import export
    ledger = seeded(tmp_path)
    ledger.evidence.append(Evidence(kind=Kind.RUNTIME, identity='second', result=Result.PASS, observed=[], tree=''))
    ledger.save()
    monkeypatch.setattr(export, 'MAX_RECEIPTS', 1)
    value = export.build(tmp_path)
    assert value['coverage']['omitted_receipts'] == 1
    assert not value['coverage']['complete']
    assert value['state'] == 'UNVERIFIED'


def test_invalid_nan_timeout_is_rejected(tmp_path):
    from core.export import build
    with pytest.raises(ValueError, match='timeout'):
        build(tmp_path, timeout=float('nan'))


def explicit_runtime(root, path='README.md'):
    from core.evidence import tree_hash
    target = root / path
    target.write_text('old')
    old = time.time_ns() - 10_000_000_000
    os.utime(target, ns=(old, old))
    git = ['git', '-c', f'safe.directory={root.as_posix()}', '-c', 'user.name=Report control',
           '-c', 'user.email=report-control@example.invalid']
    for args in (['init', '-q'], ['add', path], ['commit', '-qm', 'Initial explicit input']):
        subprocess.run([*git, *args], cwd=root, check=True, capture_output=True)
    ledger = Ledger(root=root, task='migration', claims=[Claim.MIGRATION_SAFE])
    ledger.evidence = [Evidence(kind=Kind.RUNTIME, identity='observed behaviour', result=Result.PASS,
                                observed=[path], tree=tree_hash(root, [path]), at=20)]
    ledger.save()
    return target, old


def test_explicit_content_is_freshly_read_even_with_unchanged_stat(tmp_path):
    from core.export import build
    target, old = explicit_runtime(tmp_path)
    before = build(tmp_path)
    assert before['state'] == 'VERIFIED', before
    target.write_text('new')
    os.utime(target, ns=(old, old))
    value = build(tmp_path)
    assert value['receipts'][0]['freshness'] == 'stale'
    assert value['state'] == 'STALE'


def test_explicit_input_budget_prevents_verification(tmp_path):
    from core.export import build
    explicit_runtime(tmp_path)
    (tmp_path / '.elevenpowers/config.json').write_text(json.dumps({'scan': {'max_bytes': 2}}))
    value = build(tmp_path)
    assert not value['coverage']['complete']
    assert value['state'] == 'UNVERIFIED'
    assert any('explicit' in issue for issue in value['coverage']['issues'])


def test_markdown_keeps_images_links_and_emphasis_literal():
    from core.export import _text
    rendered = _text('![check](https://example.invalid/pixel) **VERIFIED** [click](target)')
    assert '![check](' not in rendered
    assert '[click](' not in rendered
    assert '**VERIFIED**' not in rendered


@pytest.mark.parametrize('other_project', [False, True])
def test_export_does_not_write_to_ambient_verification_session(tmp_path, monkeypatch, other_project):
    from core import jobs, process
    from core.export import build
    first, second = tmp_path / 'first', tmp_path / 'second'
    first.mkdir()
    second.mkdir()
    monkeypatch.setattr(process, 'run', lambda *a, **kw: subprocess.CompletedProcess(a[0], 0, 'abc\n', ''))
    with jobs.Session(first, 'active') as owner:
        before = owner.path.read_bytes()
        build(second if other_project else first)
        assert owner.path.read_bytes() == before


def test_latest_receipts_follow_timestamps_and_limit_newest_identity(tmp_path, monkeypatch):
    from core import export
    ledger = seeded(tmp_path)
    ledger.evidence[0].at = 20
    ledger.evidence += [Evidence(kind=Kind.SUITE, identity='suite', result=Result.FAIL,
                                observed=[], tree='', at=10),
                        Evidence(kind=Kind.RUNTIME, identity='older identity', result=Result.PASS,
                                 observed=[], tree='', at=5)]
    ledger.save()
    value = export.build(tmp_path)
    suite = next(e for e in value['receipts'] if e['identity'] == 'suite')
    assert suite['result'] == 'pass'
    assert suite['recorded_at'] == 20
    monkeypatch.setattr(export, 'MAX_RECEIPTS', 1)
    assert export.build(tmp_path)['receipts'][0]['identity'] == 'suite'


def test_markdown_preserves_obligation_evidence_caveats(tmp_path):
    from core.export import build, markdown
    from core.ledger import SUITE_GRAIN
    from core.obligations import Risk
    ledger = seeded(tmp_path)
    ledger.claims = [Claim.BUG_FIXED]
    ledger.risk = Risk.HIGH
    ledger.discrimination = {'tests': 'yes'}
    ledger.save()
    value = build(tmp_path)
    assert any(c['caveat'] == SUITE_GRAIN for c in value['task']['claims'][0]['checks'])
    from core.export import _text
    assert _text(SUITE_GRAIN) in markdown(value)


def test_report_deadline_exhaustion_is_explicit_and_verdicts_are_evaluated_once(tmp_path, monkeypatch):
    from core.export import build
    seeded(tmp_path)
    original = Ledger.verdicts
    calls = []
    def delayed(self):
        calls.append(1)
        time.sleep(.08)
        return original(self)
    monkeypatch.setattr(Ledger, 'verdicts', delayed)
    value = build(tmp_path, timeout=.03)
    assert not value['coverage']['complete']
    assert value['state'] == 'UNVERIFIED'
    assert any('deadline' in issue for issue in value['coverage']['issues'])
    assert len(calls) <= 1


def test_nested_fresh_view_reads_current_content_instead_of_outer_cache(tmp_path):
    from core.evidence import freshness_view, Freshness
    target, old = explicit_runtime(tmp_path, 'service.py')
    record = Ledger.load(tmp_path).evidence[0]
    with freshness_view(tmp_path):
        assert record.freshness(tmp_path) is Freshness.FRESH
        target.write_text('new')
        os.utime(target, ns=(old, old))
        with freshness_view(tmp_path):
            assert record.freshness(tmp_path) is Freshness.STALE


def test_explicit_escape_is_incomplete_without_reading_outside_project(tmp_path):
    from core.export import build
    root = tmp_path / 'project'
    root.mkdir()
    explicit_runtime(root)
    (tmp_path / 'outside.md').write_text('private outside content')
    ledger = Ledger.load(root)
    ledger.evidence[0].observed = ['../outside.md']
    ledger.save()
    value = build(root)
    assert not value['coverage']['complete']
    assert value['state'] == 'UNVERIFIED'
    assert any('explicit input' in issue for issue in value['coverage']['issues'])
