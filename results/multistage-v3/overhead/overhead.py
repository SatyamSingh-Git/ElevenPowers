"""Open problem 4 ($0): where do the ElevenPowers arm's extra minutes go?

Reads every stage transcript (native-N.jsonl) of the 120 v3 conversations and
compares the arms per stage: model and wall time, turns, output and context
tokens, tool calls by kind, calls that run ElevenPowers itself, and calls the
host refused.
"""
import collections
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[3]
V3 = ROOT / 'results' / 'multistage-v3'
BATCHES = {'b': Path('E:/ep-runs/multistage-v3-full-2026-10-30-b'), 'c': Path('E:/ep-runs/multistage-v3-full-2026-10-30-c')}
OURS = ('ElevenPowers', 'ep_verify', 'ep_review', 'ep_doctor', 'plugin/bin/ep_')


def stage(path):
    events = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    end = next((e for e in reversed(events) if e.get('type') == 'result'), None)
    if end is None:
        return None
    calls = collections.Counter()
    ours = 0
    for event in events:
        if event.get('type') != 'assistant':
            continue
        for block in event['message']['content']:
            if block.get('type') != 'tool_use':
                continue
            calls[block['name']] += 1
            command = str(block['input'].get('command', '')) if block['name'] in ('Bash', 'PowerShell') else ''
            ours += any(mark in command for mark in OURS)
    usage = end.get('usage') or {}
    return {'wall': end.get('duration_ms', 0) / 1000, 'model': end.get('duration_api_ms', 0) / 1000,
            'turns': end.get('num_turns', 0), 'output': usage.get('output_tokens', 0),
            'context': usage.get('cache_read_input_tokens', 0) + usage.get('cache_creation_input_tokens', 0),
            'cost': end.get('total_cost_usd', 0), 'calls': dict(calls), 'ours': ours,
            'refused': sum(e.get('subtype') == 'permission_denied' for e in events),
            'background': sum(e.get('subtype') == 'task_started' for e in events)}


def main():
    analysis = json.loads((V3 / 'full-analysis.json').read_text(encoding='utf-8'))
    rerun = set(json.loads((V3 / 'full-rerun-c.json').read_text(encoding='utf-8')))
    rows = []
    for row in analysis['rows']:
        folder = BATCHES['c' if row['slot'] in rerun else 'b'] / row['slot']
        # Every stage resumes one session, whose result reports model time and cost so far.
        spent = {'model': 0, 'cost': 0}
        for path in sorted(folder.glob('native-*.jsonl'), key=lambda p: int(p.stem.split('-')[1])):
            found = stage(path)
            if found:
                so_far = {key: found[key] for key in spent}
                found.update({key: so_far[key] - spent[key] for key in spent})
                spent = so_far
                rows.append({'slot': row['slot'], 'arm': row['arm'], 'stage': int(path.stem.split('-')[1]), **found})
    Path(__file__).with_name('overhead.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
    arms = sorted({r['arm'] for r in rows})
    print('stages read:', {arm: sum(r['arm'] == arm for r in rows) for arm in arms})
    print(f"{'per stage, mean':28}" + ''.join(f'{arm:>16}' for arm in arms))
    for key in ('wall', 'model', 'turns', 'output', 'context', 'cost', 'ours', 'refused', 'background'):
        print(f'{key:28}' + ''.join(f"{statistics.mean(r[key] for r in rows if r['arm'] == arm):>16.2f}" for arm in arms))
    tools = sorted({t for r in rows for t in r['calls']})
    for tool in tools:
        print(f'{"calls: " + tool:28}' + ''.join(
            f"{statistics.mean(r['calls'].get(tool, 0) for r in rows if r['arm'] == arm):>16.2f}" for arm in arms))


if __name__ == '__main__':
    main()
