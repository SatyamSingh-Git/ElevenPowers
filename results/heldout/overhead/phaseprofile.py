import collections
import glob
import json
import statistics as st

phases = collections.defaultdict(list)
spans = []
counts = collections.Counter()
for v in glob.glob('E:/ep-installed/heldout-sweep/*--assisted--*/work/.elevenpowers/verification.json'):
    data = json.load(open(v, encoding='utf-8'))
    per = collections.Counter()
    checks = data.get('checks', [])
    for c in checks:
        if c.get('finished') and c.get('started'):
            per[c['phase']] += c['finished'] - c['started']
    for p, s in per.items():
        phases[p].append(s)
    counts['runs'] += 1
    spans.append(sum(per.values()))

print(counts, 'mean check seconds per run', round(st.mean(spans), 1))
for p, v in sorted(phases.items(), key=lambda kv: -sum(kv[1])):
    print(f'{p:40s} runs={len(v):3d} mean={st.mean(v):6.1f} total={sum(v):7.1f}')
