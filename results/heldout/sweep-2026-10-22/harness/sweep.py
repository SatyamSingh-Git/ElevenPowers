"""Run every sealed held-out slot once, in protocol order; rerunning resumes after the last launched slot."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

batch = Path(sys.argv[1])
slots = json.loads((batch / 'protocol.json').read_text(encoding='utf-8'))['slots']
for number, slot in enumerate(slots, 1):
    if (batch / slot / 'result.json').exists():
        continue
    free = shutil.disk_usage(batch).free / 2 ** 30
    if free < 1:
        print(f'stopped before {slot}: {free:.2f} GiB free', flush=True)
        sys.exit(1)
    started = time.time()
    done = subprocess.run([sys.executable, '-m', 'eval.heldout_run', 'execute', '--batch', str(batch), '--slot', slot],
                          cwd='E:/ElevenPowers', capture_output=True, text=True, encoding='utf-8', errors='replace')
    (batch / f'{slot}.log').write_text(done.stdout + done.stderr, encoding='utf-8')
    path = batch / slot / 'result.json'
    record = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    print(f"{number:3}/{len(slots)} {slot:50} exit={done.returncode} {record.get('state')} resolved={record.get('resolved')} "
          f"vacuous={record.get('vacuous')} {record.get('seconds', 0):.0f}s ${record.get('cost', 0):.3f} "
          f"wall={time.time() - started:.0f}s", flush=True)
