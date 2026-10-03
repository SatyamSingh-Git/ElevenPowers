"""Generalized report-only orchestration shared by all host adapters."""
from dataclasses import asdict
import hashlib
import importlib.util
from pathlib import Path
import sys
import time
from .. import jobs
from . import engines, store
from .baseline import baseline
from .execution import Budget
from .isolation import snapshot, trial, copy_plan, fingerprint
from .model import LIMITATION, summary
from .mutations import run_candidate
from .scope import select
from .settings import settings
from .reuse import reusable, execution_stamp


def analyze(ledger, *, base=None, command=None):
    if jobs.current() is None:
        with jobs.Session(ledger.root, ledger.task):
            return analyze(ledger, base=base, command=command)
    session = jobs.current()
    if session.root != ledger.root or session.task != ledger.task:
        raise jobs.Superseded('strength session does not own this task')
    value = {'schema_version': 2, 'task': ledger.task, 'state': 'running', 'issues': [],
             'observations': [], 'fingerprint': '', 'source_fingerprint': '',
             'baseline': 'not_run', 'engine_versions': {}, 'base': base or ledger.base,
             'command': '', 'settings': {}, 'paths': [], 'recorded_at': time.time(),
             'summary': summary([]), 'attempts': 0,
             'selection': {'strategy':'changed_functions_and_hunks', 'regions':{}, 'deletion_anchors':{}},
             'command_coverage': {'scope':'recorded_command_only', 'origin':'override' if command is not None else 'configured'},
             'limitations': [LIMITATION, 'Only selected changed files and sampled engine operators are examined.',
                            'A filesystem copy is not a security sandbox for trusted project test commands.',
                            'Passing test counts cannot prove that every selected file was imported or executed.',
                            'Other test commands may detect changes left undetected by the analyzed command.']}
    item = session.queue('test strength', 'optional changed-code analysis')
    session.begin(item)
    previous = store.load(ledger.root, ledger.task)
    try:
        options = settings(ledger.config.strength)
        value['settings'] = asdict(options)
        value['command'] = command if command is not None else options.command or ledger.config.command_for('tests')
        deadline = min(time.monotonic()+options.seconds, session.budget.deadline - 2)
        budget = Budget(deadline, options.max_mutants)
        store.save(ledger.root, value)
        if not options.enabled or not ledger.config.verifies:
            value['state'] = 'disabled'
            return value
        scope = select(ledger.root, value['base'], deadline,
                       opened_dirty=ledger.opened_dirty if base is None else ())
        value.update(paths=scope.paths, source_fingerprint=scope.fingerprint)
        value['selection'].update(regions={p:scope.regions.get(p,[]) for p in scope.paths},
                                  deletion_anchors=scope.deletions)
        value['issues'].extend(scope.issues)
        if scope.issues:
            value['state'] = 'incomplete'
            return value
        value['issues'].extend(scope.coverage_issues)
        if not scope.paths:
            value['state'] = 'incomplete' if value['issues'] else 'not_applicable'
            return value
        py = [p for p in scope.paths if Path(p).suffix == '.py']
        js = [p for p in scope.paths if Path(p).suffix != '.py']
        adapters = []
        if py:
            if options.python or importlib.util.find_spec('cosmic_ray'):
                adapters.append(('cosmic-ray', py, engines.cosmic, options.python or sys.executable))
            else:
                value['issues'].append('optional Cosmic Ray 8.7.0 is not installed')
        if js:
            engine = options.stryker or str(ledger.root / 'node_modules/@stryker-mutator/instrumenter')
            if Path(engine).is_dir():
                adapters.append(('stryker', js, engines.stryker, engine))
            else:
                value['issues'].append('optional Stryker instrumenter 9.5.1 is not installed')
        if not adapters:
            value['state'] = 'unavailable'
            return value
        with snapshot(ledger.root, options, deadline) as copied:
            if any(hashlib.sha256((copied.root/p).read_bytes()).hexdigest() != digest
                   for p,digest in scope.source_hashes.items()):
                value['issues'].append('selected source changed before its analysis snapshot')
                value['state'] = 'incomplete'
                return value
            value['fingerprint'] = execution_stamp(copied.stamp)
            versions = {}
            for name, paths, generate, executable in adapters:
                if name == 'cosmic-ray':
                    from .execution import execute
                    import json
                    probe = execute([executable, '-c', 'import importlib.metadata; print(importlib.metadata.version("cosmic-ray"))'],
                                    copied.root, budget, 5, shell=False)
                    versions[name] = probe.stdout.strip() if probe.status == 'complete' and not probe.returncode else ''
                else:
                    import json
                    try:
                        versions[name] = json.loads((Path(executable)/'package.json').read_text(encoding='utf-8'))['version']
                    except (OSError, ValueError, KeyError):
                        versions[name] = ''
            if not value['issues'] and reusable(previous, task=ledger.task, base=value['base'],
                    command=value['command'], settings=value['settings'], fingerprint=value['fingerprint'],
                    paths=value['paths'], versions=versions):
                value = previous
                return value
            with trial(copied, options, deadline) as test_root:
                tested = baseline(value['command'], test_root, ledger.root, budget, options.test_seconds)
            value['baseline'] = tested.status
            if tested.status != 'passed':
                value['issues'].append(tested.reason)
                value['state'] = 'incomplete'
                return value
            store.save(ledger.root, value)
            for index, (name, paths, generate, executable) in enumerate(adapters):
                if budget.attempts >= budget.maximum:
                    value['issues'].append('mutation attempt limit left a language unexamined')
                    break
                try:
                    # Reserve attempts for later language producers instead of
                    # letting the first language exhaust the shared budget.
                    remaining = budget.maximum - budget.attempts
                    later_files = sum(len(a[1]) for a in adapters[index:])
                    share = max(1, remaining * len(paths) // later_files)
                    producer_budget = Budget(budget.deadline, share)
                    candidates, version = generate(copied.root, paths, executable, producer_budget,
                                                   {p:scope.regions[p] for p in paths})
                    value['engine_versions'][name] = version
                    for candidate in candidates:
                        with trial(copied, options, deadline) as test_root:
                            observed = run_candidate(candidate, test_root, value['command'], budget,
                                                     options.test_seconds, original=ledger.root)
                        value['observations'].append(observed.json())
                        value['attempts'] = budget.attempts
                        value['summary'] = summary_from(value)
                        store.save(ledger.root, value)
                    if candidates.more:
                        value['issues'].append('mutation attempt limit: additional candidates were not examined')
                except ValueError as exc:
                    value['issues'].append(str(exc))
            current_paths = copy_plan(ledger.root, options, deadline)
            if current_paths != copied.paths or execution_stamp(fingerprint(ledger.root, current_paths, options, deadline)) != value['fingerprint']:
                value['issues'].append('project inputs changed during test-strength analysis')
        if value['summary']['incomplete']:
            value['issues'].append('some mutation attempts did not complete')
        if scope.deletions:
            value['issues'].append('deleted code is absent from the current source; deletion anchors are context, not examined removed behavior')
        if not value['observations']:
            value['issues'].append('no applicable mutations were produced for the selected source')
        value['state'] = 'incomplete' if value['issues'] else 'complete'
        return value
    except (OSError, ValueError, TimeoutError) as exc:
        value['issues'].append(str(exc))
        value['state'] = 'deferred' if isinstance(exc, TimeoutError) else 'incomplete'
        return value
    finally:
        value['summary'] = summary_from(value)
        store.save(ledger.root, value)
        session.finish(item, value['state'], '; '.join(value['issues'])[:512])


def summary_from(value):
    from .model import Observation
    return summary([Observation(**item) for item in value['observations']])


def consider(ledger):
    """Automatic completion work. Individual mutations never enter agent feedback."""
    if not ledger.config.verifies:
        return
    try:
        if settings(ledger.config.strength).enabled:
            analyze(ledger)
    except (OSError, ValueError, jobs.Busy, jobs.Superseded):
        # Advisory execution/persistence must not change the completion verdict.
        # A bounded fixed note lets a human distinguish absence from success.
        ledger.note('test strength incomplete', 'optional analysis could not finish or save its observation')
