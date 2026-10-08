"""Versioned independent regrading of saved staged sources; no model calls."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from .preservation import LIMITS, _read, _safe, _write
from .preservation_cases import case
from .preservation_oracles import grade

EXPECTED = {'queue-ordinary', 'queue-assisted', 'inventory-ordinary', 'inventory-assisted'}


def publish(destination, selection):
    if not selection or set(selection) - EXPECTED:
        raise ValueError('select only the four frozen slots')
    out = Path(destination).absolute()
    if out.exists() or out.is_symlink() or any(p.is_symlink() for p in out.parents):
        raise ValueError('new unlinked archive directory required')
    out.mkdir(parents=True)
    summary = {'schema': 1, 'state': 'incomplete', 'selected_slots': list(selection),
               'pairs': [], 'paired_correctness_advantage_observed': False,
               'linked_correction_observed': False, 'limits': LIMITS,
               'regrader_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    saved = {}
    for slot, batch in selection.items():
        batch = Path(batch).resolve(strict=True)
        folder = _safe(batch, slot)
        original = _read(folder / 'result.json')
        raw = _safe(folder, 'result.json').read_bytes()
        value = {'original_sha256': hashlib.sha256(raw).hexdigest(), 'original': original,
                 'protocol_sha256': hashlib.sha256((batch / 'protocol.json').read_bytes()).hexdigest(),
                 'state': 'incomplete', 'regrades': []}
        _write(out / f'{slot}-protocol.json', _read(batch / 'protocol.json'))
        definition = case(slot.rsplit('-', 1)[0])
        try:
            if original.get('slot') != slot:
                raise ValueError('record slot mismatch')
            stages = original['stages']
            if len(stages) > 2 or [s['stage'] for s in stages] != list(range(1, len(stages) + 1)):
                raise ValueError('invalid stage order')
            for item in stages:
                stage = item['stage']
                source = _read(_safe(folder, f'source-{stage}.json'))
                if set(source) != set(definition['production']):
                    raise ValueError('unexpected production snapshot')
                if any(not isinstance(text, str) or len(text.encode()) > 256 * 1024 for text in source.values()):
                    raise ValueError('invalid source snapshot')
                if any(hashlib.sha256(text.encode()).hexdigest() != item['source_after'].get(name)
                       for name, text in source.items()):
                    raise ValueError('source snapshot identity mismatch')
                with tempfile.TemporaryDirectory(prefix='ep-preserve-regrade-') as temporary:
                    root = Path(temporary)
                    for name, text in source.items():
                        _safe(root, name).write_bytes(text.encode())
                    result = grade(definition, stage, root)
                value['regrades'].append(result)
                _write(out / f'{slot}-source-{stage}.json', source)
            if (original.get('state') == 'completed' and len(stages) == 2
                    and all(s.get('scope') == 'preserved' and s.get('state') == 'completed' for s in stages)
                    and all(g['state'] == 'graded' for g in value['regrades'])):
                value['state'] = 'regraded'
        except (OSError, ValueError, KeyError, TypeError):
            pass
        saved[slot] = value
        _write(out / f'{slot}.json', value)
    complete = set(selection) == EXPECTED and all(v['state'] == 'regraded' for v in saved.values())
    for name in ('queue', 'inventory'):
        row = {'case': name, 'ordinary': None, 'assisted': None, 'difference': None}
        for arm in ('ordinary', 'assisted'):
            value = saved.get(name + '-' + arm)
            if value and value['state'] == 'regraded':
                row[arm] = {'final_passed': value['regrades'][-1]['passed'],
                            'final_failed': value['regrades'][-1]['failed'],
                            'stage_passes': [g['passed'] for g in value['regrades']],
                            'model_seconds': round(value['original']['model_seconds'], 3),
                            'original_native_states': [s['native']['state'] for s in value['original']['stages']]}
        if row['ordinary'] and row['assisted']:
            row['difference'] = row['assisted']['final_passed'] - row['ordinary']['final_passed']
        summary['pairs'].append(row)
    summary['state'] = 'regraded' if complete else 'incomplete'
    summary['paired_correctness_advantage_observed'] = complete and any(r['difference'] > 0 for r in summary['pairs'])
    _write(out / 'summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--slot', action='append', nargs=2, metavar=('NAME', 'BATCH'), required=True)
    args = parser.parse_args()
    if len({name for name, _ in args.slot}) != len(args.slot): parser.error('duplicate slot')
    print(json.dumps(publish(args.destination, dict(args.slot)), indent=2))


if __name__ == '__main__':
    main()
