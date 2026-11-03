"""Paid A/B, one-stage sessions: the same v3 stage with ElevenPowers' hooks in the old
encoded form and in the new plain form. Records cost, per-call hook-inclusive spans,
and the runtime's own per-event received/processed/error counts.

Usage: hook_form_ab.py <new scratch dir> [encoded|plain ...]   (order as given)"""
import collections
from datetime import datetime
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from core.config import Config, save
from core.hosts.setup import install, invocation, invocation_args
from eval import subscription

HERE = Path(sys.argv[1]).resolve()
HERE.mkdir(parents=True, exist_ok=True)
START = Path('E:/ep-runs/multistage-v3-full-2026-10-30-b/clinic_booking--elevenpowers--0/snapshots/0')
case = json.loads((REPO / 'eval/multistage_v3/clinic_booking/case.json').read_text(encoding='utf-8'))
prompt = case['stages'][0]['request'] + "\n\nI won't be around to answer questions while you work on this, so make any decisions yourself and finish the request in this turn."


def seconds(stamp):
    return datetime.fromisoformat(stamp.replace('Z', '+00:00')).timestamp()


run = time.strftime('%H%M%S')
for form in (sys.argv[2:] or ['encoded', 'plain']):
    work = HERE / f'ab-{form}-{run}'
    shutil.copytree(START, work)
    save(work, Config(profile='guide', commands={'tests': 'python -m pytest tests -q'}))
    path = install('claude', work, sys.executable, REPO)
    config = json.loads(path.read_text())
    if form == 'encoded':
        for entries in config['hooks'].values():
            for entry in entries:
                for handler in entry['hooks']:
                    handler['command'] = invocation(invocation_args(handler['command']))
        path.write_text(json.dumps(config, indent=2))
    for args in (['init', '-q'], ['add', '-A'], ['-c', 'user.name=p', '-c', 'user.email=p@p', 'commit', '-qm', 'base']):
        subprocess.run(['git', *args], cwd=work, check=True, capture_output=True)
    args = subscription.command('claude', 'claude', work, prompt, model='claude-sonnet-5-5')
    args[args.index('--output-format') + 1] = 'stream-json'
    args.append('--verbose')
    started = time.perf_counter()
    done = subprocess.run(args, cwd=work, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=900,
                          encoding='utf-8')
    wall = time.perf_counter() - started
    (HERE / f'ab-{form}-{run}.jsonl').write_text(done.stdout, encoding='utf-8')
    events = [json.loads(line) for line in done.stdout.splitlines() if line.startswith('{')]
    end = next(e for e in reversed(events) if e.get('type') == 'result')
    asked, calls, previous = {}, collections.defaultdict(list), float('-inf')
    for event in events:
        content = event.get('message', {}).get('content') if event.get('timestamp') else None
        for block in content if isinstance(content, list) else []:
            if block.get('type') == 'tool_use':
                asked[block['id']] = (seconds(event['timestamp']), block['name'])
            elif block.get('type') == 'tool_result' and block.get('tool_use_id') in asked:
                begun, name = asked.pop(block['tool_use_id'])
                finished = seconds(event['timestamp'])
                calls[name].append(finished - max(begun, previous))
                previous = finished
    phases = json.loads((work / '.elevenpowers/integrations.json').read_text())['claude']['phases']
    tests = subprocess.run([sys.executable, '-m', 'pytest', 'tests', '-q'], cwd=work, capture_output=True, text=True,
                           env={**__import__('os').environ, 'PYTHONPATH': 'src'})
    print(f"== {form}: wall {wall:.0f} s, model {end.get('duration_api_ms', 0) / 1000:.0f} s, "
          f"turns {end.get('num_turns')}, cost ${end.get('total_cost_usd', 0):.3f}, "
          f"init plugins {[p.get('name') for e in events if e.get('subtype') == 'init' for p in e.get('plugins', [])]}")
    for name, spans in sorted(calls.items()):
        print(f"   {name:6} n={len(spans):2} median {statistics.median(spans):.2f} s")
    for event, phase in sorted(phases.items()):
        print(f"   {event:18} received {phase.get('received')} processed {phase.get('processed')} errors {phase.get('errors', 0)}")
    print(f"   tests after: {tests.stdout.strip().splitlines()[-1] if tests.stdout.strip() else tests.stderr[-200:]}")
