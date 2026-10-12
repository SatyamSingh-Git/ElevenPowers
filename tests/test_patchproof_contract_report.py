import json
import time

import pytest

from test_patchproof_openapi import engine, project, spec


@pytest.mark.parametrize('revised,result', [(spec(), 'pass'), (spec({}), 'fail')])
def test_saved_contract_in_bundle_is_fresh_without_execution(tmp_path, engine, revised, result, monkeypatch):
    from core.patchproof.openapi import check
    from core.patchproof.report import build, markdown
    root = project(tmp_path, revised)
    check(root, 'api', engine)
    # Actual checker ran first; exporting must not launch another one.
    import core.patchproof.openapi as runner
    monkeypatch.setattr(runner, 'run', lambda *a, **k: pytest.fail('report executed checker'))
    value = build(root)
    row = value['contracts']['checks'][0]
    assert row['result'] == result and row['freshness'] == 'fresh'
    assert row['association'] == 'bound', value
    assert row['execution'] == 'complete'
    assert row['producer']['version'] == '1.33.0' and 'executable' not in row['producer']
    assert str(engine) not in json.dumps(value)
    assert 'OpenAPI backward compatibility' in markdown(value)


def test_absent_corrupt_and_stale_inputs_are_visible(tmp_path, engine):
    from core.patchproof.openapi import check
    from core.patchproof.report import build
    root = project(tmp_path)
    assert build(root)['contracts']['checks'][0]['state'] == 'absent'
    check(root, 'api', engine)
    (root / 'api.json').write_text(json.dumps(spec({})))
    value = build(root)['contracts']['checks'][0]
    assert value['freshness'] == 'stale' and value['association'] == 'unavailable'
    (root / '.elevenpowers/contracts.json').write_text('{broken')
    value = build(root)['contracts']
    assert not value['complete'] and value['issues']
    assert value['checks'][0]['state'] == 'unavailable'


def test_changed_manifest_and_range_do_not_reuse_bound_result(tmp_path, engine):
    from core.patchproof.openapi import check
    from core.patchproof.report import build
    root = project(tmp_path)
    check(root, 'api', engine)
    row = build(root, 'HEAD', 'HEAD')['contracts']['checks'][0]
    assert row['association'] == 'unavailable'
    path = root / 'elevenpowers.contracts.json'
    path.write_text(path.read_text() + '\n')
    assert build(root)['contracts']['checks'][0]['freshness'] == 'stale'


def test_changed_engine_and_state_movement_invalidate_association(tmp_path, engine, monkeypatch):
    import shutil
    from core.patchproof.openapi import check
    from core.patchproof.contract_report import inspect
    from core.patchproof.identity import collect
    local_engine = tmp_path.parent / (tmp_path.name + '.exe')
    shutil.copyfile(engine, local_engine)
    local_engine.chmod(0o755)
    root = project(tmp_path)
    check(root, 'api', local_engine)
    local_engine.write_bytes(local_engine.read_bytes() + b'changed')
    value = inspect(root, collect(root), time.monotonic() + 30)
    assert value['checks'][0]['freshness'] == 'stale'


def test_incomplete_receipt_remains_unknown(tmp_path):
    from core.patchproof.openapi import check
    from core.patchproof.report import build
    root = project(tmp_path)
    check(root, 'api', root / 'missing', seconds=0)
    row = build(root)['contracts']['checks'][0]
    assert row['state'] == 'incomplete' and row['result'] == 'unknown'


def test_real_state_movement_is_detected(tmp_path, engine, monkeypatch):
    from core.patchproof.openapi import check
    import core.patchproof.contract_report as reports
    from core.patchproof.identity import collect
    root = project(tmp_path)
    check(root, 'api', engine)
    stamp, calls = reports._stamp, []

    def moved(project_root):
        calls.append(1)
        if len(calls) == 2:
            path = root / '.elevenpowers/contracts.json'
            path.write_text(path.read_text() + '\n')
        return stamp(project_root)

    monkeypatch.setattr(reports, '_stamp', moved)
    value = reports.inspect(root, collect(root), time.monotonic() + 30)
    assert not value['complete'] and value['checks'][0]['association'] == 'unavailable'
