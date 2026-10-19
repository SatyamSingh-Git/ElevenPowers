"""Actual declared checks through the real launchers, never model acceptance."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import time

from core.config import Config, save
from core.declared_completion import rows
from core.feedback_delivery import inspect
from core.hosts.acceptance import JS_SOURCE, JS_TEST
from core.hosts.provenance import fingerprint
from core.hosts.setup import PATHS, install
from core.ledger import Ledger
from core.process import run
from core.report import end_report
from .advice_delivery import EVENTS, SOURCE, _callback

PYTHON_SOURCE = 'def accepts(value):\n    return value > 10\n'
PYTHON_TEST = '''import time
from pathlib import Path
from app import accepts

def test_contract():
    if Path('wait.flag').exists():
        print('Waiting for intentional interruption', flush=True)
        time.sleep(60)
    assert not accepts(9) and accepts(10) and accepts(11)
'''
OWNED = SOURCE / 'plugin/bin/ep_check.py'


def _project(root, host, language):
    root.mkdir(parents=True)
    if language == 'python':
        app, test = 'app.py', 'test_app.py'
        (root / app).write_text(PYTHON_SOURCE, encoding='utf8')
        (root / test).write_text(PYTHON_TEST, encoding='utf8')
        command = f'"{sys.executable}" -m pytest -q -p no:cacheprovider {test}'
    else:
        app = 'app.mjs'
        (root / app).write_text(JS_SOURCE, encoding='utf8')
        (root / 'check.test.mjs').write_text(JS_TEST, encoding='utf8')
        command = f'"{shutil.which("node")}" --test check.test.mjs'
    save(root, Config(profile='guide', commands={'tests': command}, auto_detect=False, strength={'enabled': False}))
    install(host, root, sys.executable, SOURCE)
    Ledger(root=root, task='declared-closure-control').save()
    return root / app, command


def _shell(command, root, seconds=60):
    done = run(command, cwd=root, shell=True, timeout=seconds,
               env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    return done.stdout + done.stderr, done.returncode


def case(root, host, language, mode):
    started = time.monotonic()
    root = Path(root).absolute()
    app, command = _project(root, host, language)
    callbacks = [_callback(root, host, mode, EVENTS[host][0])]
    declared = []

    def observe():
        declared.append(rows(Ledger.load(root))[0].state)

    def owned(*extra):
        invocation = f'"{sys.executable}" "{OWNED}" tests --project "{root}"' + ''.join(' ' + arg for arg in extra)
        output, code = _shell(invocation, root)
        callbacks.append(_callback(root, host, mode, EVENTS[host][1], command=invocation, output=output, code=code,
                                   tool_use_id=f'owned-{len(callbacks)}'))
        observe()
        return code, inspect(Ledger.load(root))

    observe()
    app.write_text(app.read_text().replace('value > 10', 'value >= 10'))
    output, code = _shell(command, root)
    callbacks.append(_callback(root, host, mode, EVENTS[host][1], command=command + ' 2>&1 | tail -15',
                               output=output, code=code, tool_use_id='generic'))
    observe()
    generic = inspect(Ledger.load(root))
    passed = owned()
    app.write_text(app.read_text().replace('value >= 10', 'value > 10'))
    observe()
    failed = owned()
    (root / 'wait.flag').write_text('intentional bounded interruption\n')
    interrupted = owned('--seconds', '2')
    (root / 'wait.flag').unlink()
    followups = [view['followups'][0]['state'] if view['followups'] else 'no-emission'
                 for _, view in (passed, failed, interrupted)]
    report = end_report(Ledger.load(root))
    native = mode == 'native-control'
    requirements = {
        'generic_command_passed': code == 0,
        'owned_exits': [passed[0], failed[0], interrupted[0]] == [0, 1, 2],
        'callbacks_processed': all(row['exit'] == 0 for row in callbacks),
        'declared_states': declared == ['ABSENT', 'ABSENT', 'CURRENT', 'STALE', 'FAILED', 'INCOMPLETE'],
        'delivery_stage': generic['state'] == ('emitted' if native else 'intent') and generic['intents'] == 1,
        'followup_states': followups == (['current', 'failed', 'incomplete'] if native else ['no-emission'] * 3),
        'report_annex': 'INCOMPLETE tests' in report and 'model consumption unproven' in report,
        'no_consumption_claim': all(view['model_consumption'] == 'unproven'
                                    for view in (generic, passed[1], failed[1], interrupted[1])),
    }
    return {'host': host, 'language': language, 'mode': mode, 'qualified': all(requirements.values()),
            'requirements': requirements, 'declared': declared, 'delivery_after_generic': generic['state'],
            'followups': followups, 'model_consumption': interrupted[1]['model_consumption'],
            'callbacks': callbacks, 'model_calls': 0, 'seconds': round(time.monotonic() - started, 3)}


def exercise(destination, *, hosts=tuple(PATHS), languages=('python', 'javascript'),
             modes=('replay', 'native-control')):
    destination = Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('exercise destination must be new')
    if not hosts or set(hosts) - set(PATHS) or set(languages) - {'python', 'javascript'} or \
            set(modes) - {'replay', 'native-control'}:
        raise ValueError('unsupported exercise selection')
    destination.mkdir(parents=True)
    value = {'schema': 1, 'runtime': fingerprint(), 'model_calls': 0, 'installed_acceptance': False,
             'observations': [], 'unavailable': [], 'qualified': False,
             'limits': ['Native-control means synthetic launcher ingress, not an installed agent session.',
                        'The generic command is reported to the launcher with a filter it did not run; its output is the unfiltered actual output.',
                        'A later exact receipt is temporal correlation, never proof that a model read or followed feedback.']}
    for language in languages:
        if language == 'javascript' and not shutil.which('node'):
            value['unavailable'].append('Node unavailable')
            continue
        for host in hosts:
            for mode in modes:
                value['observations'].append(case(destination / f'{language}-{host}-{mode}', host, language, mode))
                (destination / 'summary.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf8')
    value['qualified'] = (not value['unavailable'] and
                          len(value['observations']) == len(languages) * len(hosts) * len(modes) and
                          all(row['qualified'] for row in value['observations']) and fingerprint() == value['runtime'])
    (destination / 'summary.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf8')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    value = exercise(parser.parse_args().destination)
    print(json.dumps(value, indent=2))
    return 0 if value['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
