"""Explicit declared identities only; missing mappings retain broad coverage."""
import hashlib

from ..redact import scrub
from .collection import digest


def command_key(command):
    command=command.strip()
    # A parser may already have scrubbed this spelling. Neither a raw secret
    # nor its lossy public replacement can identify an exact scoped command.
    if scrub(command)!=command or 'REDACTED' in command:
        return None
    return hashlib.sha256(command.encode()).hexdigest()


def project(observed, command='', *, declared=False):
    if observed.get('scope') is not None:
        return observed
    key=command_key(command) if declared and command else None
    candidate=next((s for s in observed.get('scopes',[]) if s['command']==key),None)
    if candidate is None:
        return observed
    return selected(observed,candidate)


def selected(observed,candidate):
    scope={k:candidate[k] for k in ('command','witnesses')}
    rows=[w for w in observed['witnesses'] if w['id'] in scope['witnesses']]
    available=(len(rows)==len(scope['witnesses']) and all(w['state']=='available' for w in rows))
    return {**observed,'state':'available' if available else 'incomplete',
            'fingerprint':digest([scope,[(w['id'],w['scope_fingerprint']) for w in rows]]) if available else None,
            'witnesses':rows,'scope':scope,
            'issues':[i for w in rows for i in w['issues']]}


def closing_affected(qualification,scan):
    before=getattr(scan,'external_before',None)
    after=getattr(scan,'external_after',None)
    if before is None or after is None: return True
    scope=(qualification or {}).get('scope')
    if scope is not None:
        for observed in (before,after):
            if scope not in observed.get('scopes',[]): return True
        before,after=selected(before,scope),selected(after,scope)
    return (after['state']=='incomplete' or before['state']!=after['state']
            or before['fingerprint']!=after['fingerprint'])


def invalidate_report(value,scan,*,unknown=False):
    """Propagate an external closing gap into public rows and their consumers."""
    if value is None: return
    message='external input final inspection is unavailable or changed'
    affected=set()
    for receipt in value['receipts']:
        if not unknown and not closing_affected(receipt['external_inputs'],scan): continue
        receipt['external_inputs'].update(state='incomplete')
        receipt['external_inputs']['issues'].append(message)
        if unknown: receipt['external_inputs']['current']=None
        if receipt['freshness']=='fresh': receipt['freshness']='stale'
        affected.add(receipt['identity'])
    value['coverage']['complete']=False
    value['coverage']['issues']=list(dict.fromkeys([*value['coverage']['issues'],message]))
    if value['state']!='CONTRADICTED': value['state']='UNVERIFIED'
    for claim in value['task']['claims']:
        selected=[c for c in claim['checks'] if unknown or c['evidence'] in affected]
        if selected and claim['state']!='CONTRADICTED': claim['state']='UNVERIFIED'
        for check in selected:
            if check['freshness']=='fresh': check['freshness']='stale'
            check['caveat']='; '.join(filter(None,[check['caveat'],message]))
    if value.get('milestones') is not None:
        from ..milestones.report import invalidate_inputs
        invalidate_inputs(value['milestones'],[message],scan=None if unknown else scan)
    value['next_actions']=list(dict.fromkeys([message,*value['next_actions']]))


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
