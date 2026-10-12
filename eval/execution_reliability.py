"""Bounded, model-free repetitions of retained execution reliability controls."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from core.process import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repetitions', type=int, default=20)
    parser.add_argument('--seconds', type=int, default=240)
    args = parser.parse_args()
    if not 1 <= args.repetitions <= 50 or not 1 <= args.seconds <= 600:
        parser.error('repetitions must be 1–50 and seconds 1–600')
    root = Path(__file__).resolve().parents[1]
    tests = ['tests/test_process.py::test_keyboard_interrupt_cleans_tree_before_reraising',
             'tests/test_process.py::test_sigterm_cleans_tree_in_main_thread',
             'tests/test_process.py::test_real_interrupt_during_creation_handoff_cleans_created_process',
             'tests/test_process.py::test_cancelled_creation_waits_for_original_kernel_handle',
             'tests/test_host_setup.py::test_codex_setup_launches_quoted_paths']
    started = time.monotonic()
    for index in range(args.repetitions):
        remaining = args.seconds - (time.monotonic() - started)
        if remaining <= 0:
            print(json.dumps({'state': 'incomplete', 'completed': index, 'reason': 'budget exhausted'}))
            return 2
        with tempfile.TemporaryDirectory(prefix='ep-execution-reliability-') as directory:
            command = [sys.executable, '-m', 'pytest', '-q', *tests,
                       '--basetemp', str(Path(directory) / 'cases')]
            try:
                done = run(command, cwd=root, timeout=remaining, shell=False)
            except (OSError, subprocess.SubprocessError) as error:
                print(json.dumps({'state': 'incomplete', 'completed': index,
                                  'reason': type(error).__name__}))
                return 2
            print(json.dumps({'repetition': index + 1, 'platform': os.name,
                              'exit_code': done.returncode,
                              'elapsed_seconds': round(time.monotonic() - started, 3)}), flush=True)
            if done.returncode:
                print(done.stdout)
                print(done.stderr, file=sys.stderr)
                return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
