import json
import time

import pytest

from core.evidence import source_snapshot
from core.patchproof.identity import collect
from tests.test_patchproof_identity import git, commit


@pytest.fixture
def project(tmp_path):
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'config', 'core.autocrlf', 'false')
    (tmp_path / 'session.py').write_text('def expiry():\n    return 1\n')
    (tmp_path / 'consumer.py').write_text('from session import expiry\nvalue = expiry()\n')
    (tmp_path / 'test_session.py').write_text('from session import expiry\ndef test_expiry():\n    assert expiry() == 2\n')
    (tmp_path / 'test_import.py').write_text('import session\ndef test_import():\n    assert session\n')
    base = commit(tmp_path, 'base')
    (tmp_path / 'session.py').write_text('def expiry():\n    return 2\n')
    head = commit(tmp_path, 'patch')
    return tmp_path, base, head


def inspect_project(project, fingerprints=None, seconds=120):
    from core.patchproof.impact import inspect
    root, base, head = project
    fingerprint = source_snapshot(root, fresh=True)[1]
    return inspect(root, collect(root, base, head),
                   fingerprints or [fingerprint, fingerprint], time.monotonic() + seconds)


def test_fresh_explanations_bind_without_inventing_passing_checks(project):
    value = inspect_project(project)
    assert value['association'] == 'bound'
    assert value['patch_id'] == collect(*project)['patch_id']
    query = value['query']
    assert 'consumer.py' in {n['path'] for n in query['affected']}
    assert query['test_selection']['focused'][0]['path'] == 'test_session.py'
    assert 'test_import.py' in {n['path'] for n in query['test_selection']['fallback']}
    assert query['test_selection']['safe_to_exclude_fallback'] is False
    assert all(n['explanation'] for n in query['affected'])
    assert 'result' not in value and 'receipts' not in value
    assert value['configuration']['max_depth'] == 6


def test_incompatible_evidence_snapshot_cannot_bind(project):
    value = inspect_project(project, ['other-project', 'other-project'])
    assert value['association'] == 'unavailable'
    assert 'fingerprint' in ' '.join(value['association_issues'])


def test_dirty_patch_cannot_bind_graph(project):
    (project[0] / 'session.py').write_text('def expiry():\n    return 9\n')
    assert inspect_project(project)['association'] == 'unavailable'


def test_deadline_exhaustion_is_visible(project):
    value = inspect_project(project, seconds=0)
    assert value['association'] == 'unavailable'
    assert value['state'] == 'incomplete'
    assert value['association_issues']


def test_bundle_export_separates_recommendations_from_receipts(project):
    from core.patchproof.report import build, markdown
    root, base, head = project
    value = build(root, base, head, impact=True)
    assert value['binding']['state'] == 'bound'
    assert value['impact']['association'] == 'bound'
    assert value['checks'] == [] and value['receipts'] == []
    text = markdown(value)
    assert 'ImpactGraph recommendations' in text
    assert 'test_expiry' in text and 'test_import.py' in text
    assert 'consumer.py' in text and 'calls' in text
    assert 'not execution evidence' in text


def test_default_report_does_not_scan_graph(project, monkeypatch):
    from core.patchproof import impact
    from core.patchproof.report import build
    def forbidden(*args, **kwargs):
        pytest.fail('default report must not run graph scans')
    monkeypatch.setattr(impact, 'graph_build', forbidden)
    assert build(*project)['impact']['state'] == 'not_requested'


def test_actual_cli_exports_impact_without_writing_project_state(project, tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    root, base, head = project
    before = {p.relative_to(root).as_posix(): p.read_bytes()
              for p in root.rglob('*') if p.is_file()}
    cli = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_patchproof.py'
    done = subprocess.run([sys.executable, str(cli), '--project', str(root),
                           '--base', base, '--head', head, '--impact', '--format', 'json'],
                          capture_output=True, text=True, encoding='utf-8', timeout=120)
    assert done.returncode == 0, done.stderr
    value = json.loads(done.stdout)
    assert value['impact']['association'] == 'bound'
    after = {p.relative_to(root).as_posix(): p.read_bytes()
             for p in root.rglob('*') if p.is_file()}
    assert before == after


def test_javascript_project_declared_routes_and_tests_remain_assertions(tmp_path):
    from core.patchproof.report import build, markdown
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'config', 'core.autocrlf', 'false')
    (tmp_path / 'payment.js').write_text('export const value = 1;\n')
    (tmp_path / 'checkout.js').write_text('export const checkout = 1;\n')
    (tmp_path / 'checkout.test.js').write_text('// independent project contract test\n')
    declaration = {'schema': 1, 'nodes': [
        {'id': 'route:checkout', 'kind': 'route', 'label': 'Checkout endpoint', 'path': 'checkout.js'}],
        'edges': [{'source': 'route:checkout', 'target': 'file:payment.js', 'kind': 'uses'},
                  {'source': 'file:checkout.test.js', 'target': 'route:checkout', 'kind': 'tests'}]}
    (tmp_path / 'impactgraph.json').write_text(json.dumps(declaration))
    base = commit(tmp_path, 'base')
    (tmp_path / 'payment.js').write_text('export const value = 2;\n')
    head = commit(tmp_path, 'patch')
    value = build(tmp_path, base, head, impact=True)
    assert value['impact']['association'] == 'bound'
    query = value['impact']['query']
    route = next(n for n in query['affected'] if n['id'] == 'route:checkout')
    assert route['category'] == 'declared'
    assert all(e['origin'] == 'declared' for e in route['explanation'])
    test = next(n for n in query['test_selection']['focused'] if n['path'] == 'checkout.test.js')
    assert [e['kind'] for e in test['explanation']] == ['tests', 'uses']
    assert 'Checkout endpoint' in markdown(value)
    assert value['receipts'] == []


def test_optional_adapter_failure_does_not_hide_other_receipts(project, monkeypatch):
    from core.patchproof import impact
    from core.patchproof.report import build
    from tests.test_patchproof_report import seed
    seed(project[0])
    def failed(*args, **kwargs):
        raise ValueError('private unexpected engine output')
    monkeypatch.setattr(impact, 'graph_build', failed)
    value = build(*project, impact=True)
    assert value['binding']['state'] == 'bound'
    assert value['receipts'][0]['association'] == 'bound'
    assert value['impact']['association'] == 'unavailable'
    assert 'private unexpected engine output' not in json.dumps(value)


@pytest.mark.parametrize('mode', ['empty', 'deleted', 'renamed', 'wrong_head'])
def test_patch_scope_variants_keep_unknown_paths_visible(project, mode):
    from core.patchproof.report import build
    root, base, head = project
    if mode == 'empty':
        value = build(root, head, head, impact=True)
        assert value['impact']['state'] == 'empty'
        assert value['impact']['query'] is None
    elif mode == 'wrong_head':
        value = build(root, base, base, impact=True)
        assert value['impact']['association'] == 'unavailable'
    else:
        if mode == 'deleted':
            (root / 'session.py').unlink()
        else:
            git(root, 'mv', 'session.py', 'expiry.py')
        newer = commit(root, mode)
        value = build(root, head, newer, impact=True)
        query = value['impact']['query']
        assert 'session.py' in query['requested']
        assert query['coverage']['complete'] is False
        assert any('session.py' in issue for issue in query['coverage']['issues'])
        if mode == 'renamed':
            assert 'expiry.py' in query['requested']


def test_large_patch_reports_omitted_paths(project):
    root, base, head = project
    for i in range(257):
        (root / f'file_{i}.py').write_text('value = 0\n')
    newer = commit(root, 'large patch')
    value = inspect_project((root, head, newer))
    assert value['omitted_paths'] == 1
    assert value['association'] == 'unavailable'
    assert len(value['query']['requested']) == 256


def test_configuration_change_during_graph_invalidates_receipt_binding(project, monkeypatch):
    from core.patchproof import impact
    from core.patchproof.report import build
    original = impact.graph_build
    (project[0] / '.git/info/exclude').write_text('.elevenpowers/\n')
    calls = []
    def changed(root, **kwargs):
        if not calls:
            (root / '.elevenpowers').mkdir(exist_ok=True)
            (root / '.elevenpowers/config.json').write_text('{"commands":{"tests":"new-command"}}')
            calls.append(True)
        return original(root, **kwargs)
    monkeypatch.setattr(impact, 'graph_build', changed)
    value = build(*project, impact=True)
    assert value['binding']['state'] == 'unavailable'
    assert value['impact']['association'] == 'unavailable'


@pytest.mark.parametrize('change', ['source', 'declaration', 'configuration'])
def test_moving_graph_inputs_are_not_spliced_into_patch(project, monkeypatch, change):
    from core.patchproof import impact
    original = impact.graph_build
    calls = []
    def moving(root, **kwargs):
        value = original(root, **kwargs)
        if not calls:
            if change == 'source':
                (root / 'consumer.py').write_text('value = 0\n')
            elif change == 'declaration':
                (root / 'impactgraph.json').write_text('{"schema":1}')
            else:
                (root / '.elevenpowers').mkdir(exist_ok=True)
                (root / '.elevenpowers/config.json').write_text('{"scan":{"max_files":1}}')
            calls.append(True)
        return value
    monkeypatch.setattr(impact, 'graph_build', moving)
    value = inspect_project(project)
    assert value['association'] == 'unavailable'
    assert value['association_issues']
