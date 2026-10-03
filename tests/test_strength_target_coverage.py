"""End-to-end coverage for removed files and mixed-language projects."""
import sys
import pytest
from core.config import Config
from core.ledger import Ledger
from core.strength.runner import analyze
from test_strength import repository, stryker_path


def test_entire_deleted_production_file_is_incomplete_coverage(tmp_path):
    base = repository(tmp_path)
    (tmp_path/'a.py').unlink()
    ledger = Ledger(root=tmp_path, task='removed', base=base)
    ledger._config = Config()
    value = analyze(ledger)
    assert value['state'] == 'incomplete'
    assert any('removed production source' in issue and 'a.py' in issue for issue in value['issues'])
    assert value['observations'] == []


def test_small_mixed_language_budget_reserves_a_turn_for_both_engines(tmp_path):
    engine = stryker_path()
    base = repository(tmp_path)
    (tmp_path/'a.py').write_text('def positive(x):\n    return x > 0\n')
    (tmp_path/'b.mjs').write_text('export function positive(x) {\n  return x > 0;\n}\n')
    (tmp_path/'test_a.py').write_text('from a import positive\ndef test_value():\n    assert positive(2)\n')
    (tmp_path/'b.test.mjs').write_text("import {test} from 'node:test'; import assert from 'node:assert/strict'; import {positive} from './b.mjs'; test('positive', () => assert.equal(positive(2),true));\n")
    ledger = Ledger(root=tmp_path, task='mixed', base=base)
    ledger._config = Config(commands={'tests':f'"{sys.executable}" -m pytest -q -p no:cacheprovider && node --test b.test.mjs'},
                            strength={'python':sys.executable,'stryker':engine,'max_mutants':2,
                                      'seconds':50,'test_seconds':15})
    value = analyze(ledger)
    assert value['baseline'] == 'passed'
    assert value['engine_versions'] == {'cosmic-ray':'8.7.0','stryker':'9.5.1'}
    assert {o['path'] for o in value['observations']} == {'a.py','b.mjs'}
    assert value['attempts'] == 2
