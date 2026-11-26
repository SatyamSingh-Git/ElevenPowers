"""Run every sealed four-arm slot once, two workers on alternate slots; a rerun resumes after launched slots.

October's driver and guard in one: launching stops after three consecutive host-side failures
(a quota cut, a plugin that stopped loading), so a systematic fault cannot consume every slot.
Usage: python sweep.py BATCH [WORKERS]
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

HOST_FAILURES = {'host_failed', 'host_incomplete', 'host_unavailable', 'authentication_or_host_unavailable',
                 'model_unqualified', 'output_limit', 'canary_failed', 'plugins_unqualified', None}
batch = Path(sys.argv[1])
workers = int(sys.argv[2]) if len(sys.argv) > 2 else 2
slots = json.loads((batch / 'protocol.json').read_text(encoding='utf-8'))['slots']
lock = threading.Lock()
state = {'streak': 0, 'stopped': ''}


def work(worker):
    for number, slot in enumerate(slots, 1):
        if number % workers != worker or (batch / slot / 'result.json').exists():
            continue
        with lock:
            if state['stopped']:
                return
        free = shutil.disk_usage(batch).free / 2 ** 30
        if free < 2:
            with lock:
                state['stopped'] = f'{free:.2f} GiB free before {slot}'
            return
        started = time.time()
        done = subprocess.run([sys.executable, '-m', 'eval.heldout_run', 'execute', '--batch', str(batch),
                               '--slot', slot], cwd='E:/ElevenPowers', capture_output=True, text=True,
                              encoding='utf-8', errors='replace')
        (batch / f'{slot}.log').write_text(done.stdout + done.stderr, encoding='utf-8')
        path = batch / slot / 'result.json'
        record = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        with lock:
            state['streak'] = state['streak'] + 1 if record.get('state') in HOST_FAILURES else 0
            print(f"{number:3}/{len(slots)} w{worker} {slot:50} exit={done.returncode} {record.get('state')} "
                  f"resolved={record.get('resolved')} vacuous={record.get('vacuous')} "
                  f"{record.get('seconds', 0):.0f}s ${record.get('cost', 0):.3f} wall={time.time() - started:.0f}s",
                  flush=True)
            if state['streak'] >= 3:
                state['stopped'] = f'three consecutive host-side failures, last {slot}: {record.get("state")}'
                return


threads = [threading.Thread(target=work, args=(k,)) for k in range(workers)]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()
if state['stopped']:
    (batch / 'stopped.txt').write_text(state['stopped'] + '\n', encoding='utf-8')
    print('stopped:', state['stopped'], flush=True)
    sys.exit(1)
print('all slots launched', flush=True)
