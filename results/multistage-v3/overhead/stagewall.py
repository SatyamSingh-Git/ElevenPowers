"""Split each v3 stage's wall time into parts, both arms, from the stage transcripts.

startup   time_to_request_ms: process start to the first model request; its
          input_hooks phase is the SessionStart and UserPromptSubmit hooks.
tools     time covered by tool calls, each from the assistant event that asked for it to the user event
          that returned it: the tool and its Pre/PostToolUse hooks.
rest      what is left of the loop between the first and last event: the model.
tail      duration_ms minus startup minus the first-to-last event span: the first
          request's wait, the Stop hook and process exit.
Same conversations as overhead.py.
"""
import collections
from datetime import datetime
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[3]
V3 = ROOT / 'results' / 'multistage-v3'
BATCHES = {'b': Path('E:/ep-runs/multistage-v3-full-2026-10-30-b'), 'c': Path('E:/ep-runs/multistage-v3-full-2026-10-30-c')}


def seconds(stamp):
    return datetime.fromisoformat(stamp.replace('Z', '+00:00')).timestamp()


def kind(block):
    if block['name'] not in ('Bash', 'PowerShell'):
        return block['name']
    command = str(block['input'].get('command', ''))
    if 'ep_check' in command:
        return 'shell: ep_check'
    if 'pytest' in command or 'unittest' in command:
        return 'shell: tests'
    return 'shell: other'


def stage(path):
    events = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    end = next((e for e in reversed(events) if e.get('type') == 'result'), None)
    stamped = [e for e in events if e.get('timestamp')]
    if end is None or not stamped or 'time_to_request_ms' not in end:
        return None
    asked, tools, calls, spans = {}, collections.Counter(), collections.defaultdict(list), []
    for event in stamped:
        for block in event.get('message', {}).get('content', []) if isinstance(event.get('message', {}).get('content'), list) else []:
            if block.get('type') == 'tool_use':
                asked[block['id']] = (seconds(event['timestamp']), kind(block))
            elif block.get('type') == 'tool_result' and block.get('tool_use_id') in asked:
                started, name = asked.pop(block['tool_use_id'])
                tools[name] += seconds(event['timestamp']) - started
                calls[name].append(seconds(event['timestamp']) - started)
                spans.append((started, seconds(event['timestamp'])))
    # Calls asked for together run together, so their spans overlap; count the union.
    covered, reach = 0.0, float('-inf')
    for started, finished in sorted(spans):
        covered += max(0.0, finished - max(started, reach))
        reach = max(reach, finished)
    wall = end['duration_ms'] / 1000
    startup = end['time_to_request_ms'] / 1000
    loop = seconds(stamped[-1]['timestamp']) - seconds(stamped[0]['timestamp'])
    return {'wall': wall, 'startup': startup,
            'input hooks': end.get('time_to_request_phases_ms', {}).get('input_hooks', 0) / 1000,
            'tools': covered, 'rest of loop': loop - covered,
            'tail': wall - startup - loop, 'calls': calls, **{'  ' + k: v for k, v in tools.items()}}


def main():
    analysis = json.loads((V3 / 'full-analysis.json').read_text(encoding='utf-8'))
    rerun = set(json.loads((V3 / 'full-rerun-c.json').read_text(encoding='utf-8')))
    rows = collections.defaultdict(list)
    for row in analysis['rows']:
        folder = BATCHES['c' if row['slot'] in rerun else 'b'] / row['slot']
        for path in folder.glob('native-*.jsonl'):
            found = stage(path)
            if found:
                rows[row['arm']].append(found)
    arms = sorted(rows)
    keys = ['wall', 'startup', 'input hooks', 'tools'] + sorted({k for a in arms for r in rows[a] for k in r if k.startswith('  ')}) + ['rest of loop', 'tail']
    print('stages:', {arm: len(rows[arm]) for arm in arms})
    print(f"{'mean seconds per stage':26}" + ''.join(f'{arm:>15}' for arm in arms) + f"{'difference':>13}")
    for key in keys:
        means = [statistics.mean(r.get(key, 0) for r in rows[arm]) for arm in arms]
        print(f'{key:26}' + ''.join(f'{m:>15.1f}' for m in means) + f'{means[0] - means[1]:>13.1f}')
    print('per call, median seconds (calls)')
    for name in sorted({k for a in arms for r in rows[a] for k in r['calls']}):
        cells = []
        for arm in arms:
            spans = [x for r in rows[arm] for x in r['calls'].get(name, [])]
            cells.append(f"{statistics.median(spans):.2f} ({len(spans)})" if spans else '-')
        print(f'  {name:24}' + ''.join(f'{c:>15}' for c in cells))
    for arm in arms:
        tails = [r['tail'] for r in rows[arm]]
        print(f'{arm} tail: median {statistics.median(tails):.1f} s, quartiles '
              f'{statistics.quantiles(tails, n=4)[0]:.1f}-{statistics.quantiles(tails, n=4)[2]:.1f} s')


if __name__ == '__main__':
    main()
