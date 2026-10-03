"""Forward and adversarial controls for changed-region strength analysis."""
from pathlib import Path


def test_strength_report_explains_relation_and_command_coverage():
    from core.export import markdown
    strength = {'state':'incomplete','freshness':'fresh',
                 'selection':{'strategy':'changed_functions_and_hunks','regions':{'a.py':[[5,5]]},'deletion_anchors':{}},
                 'command_coverage':{'scope':'recorded_command_only','origin':'override'},
                 'observations':[{'path':'a.py','line':5,'end_line':5,'operator':'change','status':'undetected',
                                  'relevance':'changed_lines','context':'edited'}]}
    # Use an actual standard export as the base, so this exercises the renderer
    # without mirroring every field of its public envelope.
    import tempfile
    from core.export import build
    with tempfile.TemporaryDirectory() as folder:
        exported=build(Path(folder))
    exported['test_strength']=strength
    text=markdown(exported)
    assert 'changed lines' in text and 'edited' in text
    assert 'other test commands may detect' in text.lower()


def test_historical_sample_stays_unattributed_and_read_only(tmp_path):
    import time
    from test_strength_target_store import record
    from core.config import Config
    from core.strength.store import save
    from core.strength.view import view
    value = record()
    value['schema_version'] = 1
    value.pop('selection'); value.pop('command_coverage')
    save(tmp_path, value)
    state = tmp_path / '.elevenpowers/strength.json'
    before = state.read_bytes()
    shown = view(tmp_path, 't', Config(), '', time.monotonic()+5)
    assert shown['selection'] == {'strategy': 'legacy_whole_files'}
    assert shown['freshness'] == 'unknown'
    assert any('no changed-function attribution' in issue for issue in shown['issues'])
    assert state.read_bytes() == before
