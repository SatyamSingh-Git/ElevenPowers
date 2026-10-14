"""Explicit declared identities only; missing mappings retain broad coverage."""
import hashlib

from ..redact import scrub
from .collection import digest


def command_key(command):
    return hashlib.sha256(scrub(command.strip()).encode()).hexdigest()


def project(observed, command='', *, declared=False):
    if observed.get('scope') is not None:
        return observed
    key=command_key(command) if declared and command else None
    candidate=next((s for s in observed.get('scopes',[]) if s['command']==key),None)
    if candidate is None:
        return observed
    scope={k:candidate[k] for k in ('command','witnesses')}
    rows=[w for w in observed['witnesses'] if w['id'] in scope['witnesses']]
    available=(len(rows)==len(scope['witnesses']) and all(w['state']=='available' for w in rows))
    return {**observed,'state':'available' if available else 'incomplete',
            'fingerprint':digest([scope,[(w['id'],w['scope_fingerprint']) for w in rows]]) if available else None,
            'witnesses':rows,'scope':scope,
            'issues':[i for w in rows for i in w['issues']]}


def for_record(observed,record):
    return project(observed,record.declared_command,declared=bool(record.declaration))


def valid(scope):
    from .definition import label
    from .receipts import hexadecimal
    if not isinstance(scope,dict) or set(scope)!={'command','witnesses'} or not hexadecimal(scope['command']):
        return False
    ids=scope['witnesses']
    if not isinstance(ids,list) or not 1<=len(ids)<=32 or any(not isinstance(w,str) for w in ids):
        return False
    try:
        return len(set(ids))==len(ids) and all(label(w)==w for w in ids)
    except ValueError:
        return False
