import collections
import glob
import json
import statistics as st
import sys
from datetime import datetime

runs = sys.argv[1]


def ts(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp()


def category(name, inp):
    if name == 'Bash':
        cmd = inp.get('command', '')
        if 'plugin\\bin' in cmd or 'plugin/bin' in cmd or 'ep_' in cmd:
            return 'bash-ep'
        if 'pytest' in cmd or 'unittest' in cmd or 'tox' in cmd:
            return 'bash-test'
        return 'bash-other'
    if name in ('Edit', 'Write', 'MultiEdit'):
        return 'edit'
    return 'read'


agg = collections.defaultdict(lambda: collections.defaultdict(list))
per_run = []
for d in sorted(glob.glob(runs + '/*')):
    arm = d.split('--')[1]
    try:
        lines = [json.loads(l) for l in open(d + '/native.jsonl', encoding='utf-8')]
    except OSError:
        continue
    res = [x for x in lines if x.get('type') == 'result']
    if not res:
        continue
    r = res[-1]
    uses = {}
    for x in lines:
        if x.get('type') == 'assistant':
            for b in x['message'].get('content', []):
                if b.get('type') == 'tool_use':
                    uses[b['id']] = (ts(x['timestamp']), category(b['name'], b.get('input', {})))
    sums = collections.Counter()
    for x in lines:
        if x.get('type') == 'user' and isinstance(x['message'].get('content'), list):
            for b in x['message']['content']:
                if isinstance(b, dict) and b.get('type') == 'tool_result' and b.get('tool_use_id') in uses:
                    start, cat = uses[b['tool_use_id']]
                    sums[cat] += ts(x['timestamp']) - start
    nonapi = (r['duration_ms'] - r['duration_api_ms']) / 1000
    a = agg[arm]
    for cat in ('edit', 'read', 'bash-test', 'bash-ep', 'bash-other'):
        a[cat].append(sums[cat])
    a['nonapi'].append(nonapi)
    a['residual'].append(nonapi - sum(sums.values()))
    per_run.append((d.split('/')[-1].split('\\')[-1], arm, round(nonapi, 1), dict((k, round(v, 1)) for k, v in sums.items())))

for arm, a in agg.items():
    print(arm, len(a['nonapi']), {k: round(st.mean(v), 1) for k, v in a.items()})
for row in sorted(per_run, key=lambda r: -r[2])[:12]:
    print(row)
