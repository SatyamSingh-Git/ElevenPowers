"""Run replicates 0-39 of the sealed Sonnet 5 batch once each, four at a time, never retrying.

The design's amendment cut the batch from 60 to 40 per arm after the harness-check slot cost $0.58
(docs/superpowers/specs/2026-11-10-rule-as-mandate-sonnet-5-design.md). Replicates 40-59 stay in the
protocol, never launched. The order is the acted-on launcher's. Usage: launch.py <sealed batch>"""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'results' / 'rule-groups-acted-on'))
from launch import WORKERS, order  # noqa: E402

KEPT = 40


def main():
    batch = Path(sys.argv[1]).resolve(strict=True)
    slots = [s for s in order(json.loads((batch / 'protocol.json').read_text(encoding='utf-8'))['slots'])
             if int(s.rsplit('--', 1)[1]) < KEPT]
    path = batch / 'launch-order.json'
    if path.exists():
        raise SystemExit('already launched; never relaunch a batch')
    path.write_text(json.dumps(slots, indent=1), encoding='utf-8')

    def execute(slot):
        done = subprocess.run([sys.executable, '-m', 'eval.rule_groups_run', 'execute', str(batch), slot],
                              cwd=ROOT, capture_output=True, text=True)
        print(slot, (done.stdout.strip().splitlines() or [done.stderr.strip()[-300:]])[-1], flush=True)

    with ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(execute, slots))


if __name__ == '__main__':
    main()
