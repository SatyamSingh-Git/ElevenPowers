"""Bounded advice after generic verification; never execution or evidence."""
import hashlib
import json
from dataclasses import asdict

from .evidence import Freshness, Kind
from .jobs import Busy, Superseded, ledger_write
from .ledger import DELIVERY, Ledger
from .parsers import DECLARED_KINDS, claims_to_run_tests

NOTE = 'declared verification feedback'


def _reserve(ledger, key, configuration):
    """Commit diagnostic intent once, independently of native receipt dedup."""
    with ledger_write(ledger.root):
        saved = Ledger.load(ledger.root)
        if saved.task != ledger.task or saved.config != configuration:
            return False
        previous = [d.get('why', '') for d in saved.decisions if d.get('what') == NOTE]
        if key in previous or sum(k.startswith(key.split(':', 1)[0]+':') for k in previous) >= 16:
            return False
        saved.note(NOTE, key)
        # Receipt delivery was already committed. This is an independent note,
        # not a second tool observation or a reason to rewrite its evidence.
        token = DELIVERY.set(None)
        try:
            saved._save_locked(expected_task=ledger.task)
        finally:
            DELIVERY.reset(token)
    return True


def feedback(ledger, records, command):
    """Suggest exact checks left unqualified by a completed generic result."""
    try:
        configuration = ledger.config
        if not configuration.speaks or not ledger.task:
            return ''
        kinds = {r.kind for r in records if not r.declaration and r.execution == 'complete'}
        if not claims_to_run_tests(command):
            kinds.discard(Kind.SUITE)
        selected = []
        for property, kind in DECLARED_KINDS.items():
            command = configuration.command_for(property)
            if not command or kind not in kinds:
                continue
            exact = [e for e in ledger.evidence if e.declaration == property and e.kind is kind
                     and e.command_identity == command]
            latest = max(exact, key=lambda e:e.at) if exact else None
            if latest and latest.execution == 'complete' and latest.freshness(ledger.root) is Freshness.FRESH:
                continue
            selected.append(property)
        if not selected:
            return ''
        from .checks import guidance
        commands = [configuration.command_for(p) for p in selected]
        all_properties = {p for p in DECLARED_KINDS if configuration.declares(p)}
        words = (guidance(ledger.root, batch=True) if set(selected) == all_properties else
                 guidance(ledger.root, commands=commands))
        if not words:
            return ''
        text = 'Generic verification recorded; refresh exact declared checks: '+', '.join(selected)+'.\n'+words
        if len(text) > 1800:
            text = ('Generic verification recorded; exact declared checks need a fresh receipt. '
                    'Owned instructions exceed the feedback bound; inspect ep_check.py --list '
                    'and run the selected property explicitly.')
        subject = hashlib.sha256(ledger.task.encode()).hexdigest()
        identity = {'declarations':list(zip(selected,commands)), 'configuration':asdict(configuration)}
        signature = hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
        return text if _reserve(ledger, subject+':'+signature, configuration) else ''
    except (OSError, ValueError, Busy, Superseded):
        return ''  # Advice cannot discard the receipt already captured by the hook.
