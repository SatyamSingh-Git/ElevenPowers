"""Stop the sweep driver after three consecutive host-side failures, so a quota cut cannot consume every slot."""
import subprocess
import sys
import time
from pathlib import Path

log = Path(sys.argv[1])
HOST_FAILURES = ('host_failed', 'host_incomplete', 'host_unavailable', 'authentication_or_host_unavailable',
                 'model_unqualified', 'output_limit', 'canary_failed', 'None')
seen, streak = 0, 0
while True:
    text = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
    # Only this run's slots: the lines before a resume marker belong to a driver that is gone.
    lines = [l for l in text.split('--- resumed')[-1].splitlines() if '/240 ' in l]
    for line in lines[seen:]:
        state = line.split(' exit=')[1].split()[1] if ' exit=' in line else ''
        streak = streak + 1 if state in HOST_FAILURES else 0
        if streak >= 3:
            subprocess.run(['powershell', '-NoProfile', '-Command',
                            "Get-CimInstance Win32_Process | ? { $_.CommandLine -match 'sweep.py' -and $_.Name -eq 'python.exe' }"
                            " | % { taskkill /PID $_.ProcessId /T /F }"], capture_output=True)
            (log.parent / 'guard-stopped.txt').write_text(f'three consecutive host failures, last: {line}\n', encoding='utf-8')
            print('guard stopped the sweep:', line, flush=True)
            sys.exit(0)
    seen = len(lines)
    alive = subprocess.run(['powershell', '-NoProfile', '-Command',
                            "(Get-CimInstance Win32_Process | ? { $_.CommandLine -match 'sweep.py' -and $_.Name -eq 'python.exe' } | measure).Count"],
                           capture_output=True, text=True).stdout.strip()
    if alive == '0':
        print('driver finished; guard exits', flush=True)
        sys.exit(0)
    time.sleep(20)
