"""Run every slot of a sealed acted-on batch once, four at a time, never retrying.

The order is fixed before the first launch: replicate blocks in turn, shuffled within each block
with a seed, so both arms and every stage are spread evenly across the run's hours and workers.
Usage: launch.py <sealed batch>"""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
WORKERS = 4


def order(slots):
    blocks = {}
    for slot in sorted(slots):
        blocks.setdefault(int(slot.rsplit('--', 1)[1]), []).append(slot)
    ordered = []
    for replicate, block in sorted(blocks.items()):
        random.Random(20261104 + replicate).shuffle(block)
        ordered += block
    return ordered


def main():
    batch = Path(sys.argv[1]).resolve(strict=True)
    slots = order(json.loads((batch / 'protocol.json').read_text(encoding='utf-8'))['slots'])
    path = batch / 'launch-order.json'
    if path.exists():
        raise SystemExit('already launched; never relaunch a batch')
    path.write_text(json.dumps(slots, indent=1), encoding='utf-8')

    def execute(slot):
        done = subprocess.run([sys.executable, '-m', 'eval.rule_groups_run', 'execute', str(batch), slot],
                              cwd=ROOT, capture_output=True, text=True)
        line = (done.stdout.strip().splitlines() or [done.stderr.strip()[-300:]])[-1]
        print(slot, line, flush=True)

    with ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(execute, slots))


if __name__ == '__main__':
    main()
