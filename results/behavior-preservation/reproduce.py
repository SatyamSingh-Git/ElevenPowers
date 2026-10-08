"""Reproduce independent source grades only; no host, model or project checks."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))
from eval.preservation_cases import case
from eval.preservation_oracles import grade

summary = json.loads((ROOT / 'summary.json').read_text(encoding='utf-8'))
for slot in summary['selected_slots']:
    saved = json.loads((ROOT / f'{slot}.json').read_text(encoding='utf-8'))
    definition = case(slot.rsplit('-', 1)[0])
    for stage, expected in enumerate(saved['regrades'], 1):
        source = json.loads((ROOT / f'{slot}-source-{stage}.json').read_text(encoding='utf-8'))
        assert set(source) == set(definition['production'])
        with tempfile.TemporaryDirectory(prefix='ep-preservation-reproduce-') as folder:
            root = Path(folder)
            for name, text in source.items():
                assert hashlib.sha256(text.encode()).hexdigest() == expected['source_sha256'][name]
                (root / name).write_bytes(text.encode())
            actual = grade(definition, stage, root)
        assert actual['oracle_sha256'] == expected['oracle_sha256']
        assert actual['state'] == expected['state'] and actual['checks'] == expected['checks']
        print(slot, stage, actual['state'], actual['passed'], 'passed,', actual['failed'], 'failed')
print('Independent source grades reproduced; native sessions and advice usefulness were not rerun.')
