"""Forward and adversarial controls for changed-region strength analysis."""
import sys
import time
from pathlib import Path
import pytest


def test_shared_analysis_persists_targeting_and_command_only_coverage(tmp_path):
    import subprocess
    from test_strength import repository
    from core.config import Config
    from core.ledger import Ledger
    from core.strength.runner import analyze
    from core.strength.store import load
    base = repository(tmp_path)
    source = 'def old(x):\n    return x > 0\n\ndef edited(x):\n    return x > 1\n'
    (tmp_path/'a.py').write_text(source)
    (tmp_path/'test_a.py').write_text('from a import edited\ndef test_value():\n    assert edited(3)\n')
    def git(*args):
        return subprocess.check_output(['git','-c',f'safe.directory={tmp_path.as_posix()}',*args],cwd=tmp_path,text=True).strip()
    git('add','.'); git('commit','-m','functions'); base = git('rev-parse','HEAD')
    (tmp_path/'a.py').write_text(source.replace('x > 1','x > 2'))
    ledger = Ledger(root=tmp_path,task='targeted',base=base)
    ledger._config = Config(commands={'tests':f'"{sys.executable}" -m pytest -q -p no:cacheprovider'},
                            strength={'python':sys.executable,'max_mutants':2,'seconds':40,'test_seconds':10})
    result = analyze(ledger)
    assert result['schema_version'] == 2
    assert result['selection']['regions'] == {'a.py':[[5,5]]}
    assert result['command_coverage'] == {'scope':'recorded_command_only','origin':'configured'}
    assert result['observations'] and all(o['context']=='edited' for o in result['observations'])
    assert load(tmp_path,'targeted')['selection'] == result['selection']
    assert (tmp_path/'a.py').read_text() == source.replace('x > 1','x > 2')


def test_changed_source_after_selection_never_reaches_baseline(tmp_path, monkeypatch):
    from test_strength import repository
    from core.config import Config
    from core.ledger import Ledger
    from core.strength import runner
    base = repository(tmp_path)
    (tmp_path/'a.py').write_text('value = 2\n')
    original = runner.select
    def selected(*args, **kwargs):
        scope = original(*args, **kwargs)
        (tmp_path/'a.py').write_text('value = 3\n')
        return scope
    monkeypatch.setattr(runner, 'select', selected)
    def unexpected(*args, **kwargs):
        pytest.fail('baseline ran after the selected source changed')
    monkeypatch.setattr(runner, 'baseline', unexpected)
    ledger = Ledger(root=tmp_path, task='race', base=base)
    ledger._config = Config(strength={'python': sys.executable})
    result = runner.analyze(ledger)
    assert result['state'] == 'incomplete' and result['baseline'] == 'not_run'
    assert any('changed before its analysis snapshot' in s for s in result['issues'])


def test_pure_deletion_is_context_and_does_not_sample_another_function(tmp_path):
    import subprocess
    from test_strength import repository
    from core.config import Config
    from core.ledger import Ledger
    from core.strength.runner import analyze
    repository(tmp_path)
    source = 'def removed(x):\n    return x > 0\n\ndef kept(x):\n    return x > 1\n'
    (tmp_path/'a.py').write_text(source)
    (tmp_path/'test_a.py').write_text('from a import kept\ndef test_value():\n    assert kept(3)\n')
    def git(*args):
        return subprocess.check_output(['git','-c',f'safe.directory={tmp_path.as_posix()}',*args],
                                       cwd=tmp_path,text=True).strip()
    git('add', '.'); git('commit', '-m', 'two functions')
    base = git('rev-parse', 'HEAD')
    (tmp_path/'a.py').write_text(source.split('\n\n')[1])
    ledger = Ledger(root=tmp_path, task='deletion', base=base)
    ledger._config = Config(commands={'tests':f'"{sys.executable}" -m pytest -q -p no:cacheprovider'},
                            strength={'python':sys.executable, 'seconds':30, 'test_seconds':10})
    result = analyze(ledger)
    assert result['baseline'] == 'passed' and result['observations'] == []
    assert result['selection']['regions'] == {'a.py': []}
    assert result['selection']['deletion_anchors'] == {'a.py': [1]}
    assert result['state'] == 'incomplete'
    assert any('not examined removed behavior' in issue for issue in result['issues'])
