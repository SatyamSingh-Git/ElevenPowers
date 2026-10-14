"""Optional execution observations; current reads cannot invent old provenance."""
import re
import time
from pathlib import Path

from .collection import capture

KEYS={'schema','state','before','after','attempt','issues'}


def hexadecimal(value):
    return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None


def valid(value):
    if not isinstance(value,dict): return False
    scoped=value.get('schema')==2
    expected=KEYS|{'scope'} if scoped else KEYS
    if scoped and 'witnesses' in value: expected=expected|{'witnesses'}
    if (set(value)!=expected or type(value.get('schema')) is not int
            or value['schema'] not in (1,2) or not isinstance(value['state'],str)
            or value['state'] not in {'bound','stale','incomplete'}
            or any(v is not None and not hexadecimal(v) for v in (value['before'],value['after']))
            or not (value['attempt']=='' or hexadecimal(value['attempt']))
            or not isinstance(value['issues'],list) or len(value['issues'])>16
            or any(not isinstance(i,str) or len(i)>192 for i in value['issues'])):
        return False
    if scoped:
        from .scopes import valid as valid_scope
        if not valid_scope(value['scope']): return False
        if 'witnesses' in value:
            rows=value['witnesses']
            if (not isinstance(rows,dict) or set(rows)!=set(value['scope']['witnesses'])
                    or any(not isinstance(row,dict) or set(row)!={'before','after'}
                           or any(v is not None and not hexadecimal(v) for v in row.values())
                           for row in rows.values())): return False
            if value['state']=='bound' and any(not hexadecimal(r['before']) or r['before']!=r['after']
                                             for r in rows.values()): return False
    if value['state']=='bound':
        return (hexadecimal(value['before']) and value['before']==value['after']
                and hexadecimal(value['attempt']) and not value['issues'])
    return True


def metadata(before,after,attempt,issues=()):
    if before['state']==after['state']=='not_configured':
        return {}
    first=before.get('fingerprint');last=after.get('fingerprint')
    first=first if hexadecimal(first) else None
    last=last if hexadecimal(last) else None
    gaps=list(dict.fromkeys(str(i)[:192] for i in issues))[:15]
    state='bound'
    if before['state']!='available' or after['state']!='available' or not first or not last:
        gaps.append('Required external input observations were unavailable or incomplete.')
    if not hexadecimal(attempt):
        gaps.append('No identified execution has paired before/after observations.')
        attempt=''
    if gaps:
        state='incomplete'
    elif first!=last:
        state='stale'
    value={'schema':1,'state':state,'before':first,'after':last,'attempt':attempt,'issues':gaps[:16]}
    scope=before.get('scope')
    if scope is not None:
        value.update(schema=2,scope=scope)
        if 'witnesses' in before:
            first_rows={w['id']:w.get('scope_fingerprint') for w in before['witnesses']}
            last_rows={w['id']:w.get('scope_fingerprint') for w in after.get('witnesses',[])}
            value['witnesses']={name:{'before':first_rows.get(name),'after':last_rows.get(name)}
                                for name in scope['witnesses']}
        if after.get('scope')!=scope and after['state']!='incomplete':
            value.update(state='stale')
    return value


def attach(records,before,after,attempt,issues=()):
    for record in records:
        from .scopes import for_record
        value=metadata(for_record(before,record),for_record(after,record),attempt,issues)
        record.external_inputs={**value,'issues':list(value['issues'])} if value else {}


def read_current(root):
    from ..evidence import _FRESHNESS_VIEW
    view=_FRESHNESS_VIEW.get()
    if view is not None and view.root==Path(root).resolve():
        return view.inputs
    return capture(root,time.monotonic()+10)


def inspect(record,root,current=None):
    stored=record.external_inputs
    value={'state':'incomplete','before':None,'after':None,'current':None,'issues':[]}
    try:
        observed=current if current is not None else read_current(root)
    except (OSError,ValueError,TimeoutError):
        value['issues'].append('Current external input inspection is unavailable.')
        return value
    value['current']=observed.get('fingerprint')
    if observed['state']=='not_configured' and stored=={}:
        value['state']='not_configured'
        return value
    if not valid(stored):
        value['issues'].append('Saved external execution observations are absent or malformed.')
        return value
    if stored['schema']==2:
        from .scopes import for_record
        observed=for_record(observed,record)
        value.update(current=observed.get('fingerprint'),scope=stored['scope'])
        if observed['state']=='incomplete' and observed.get('scope') is None:
            value['issues'].append('Current command scope is unavailable; its change cannot be established.')
            return value
        if observed.get('scope')!=stored['scope']:
            value.update(state='stale',issues=['Declared command witness scope changed or was removed.'])
            return value
        rows={w['id']:w for w in observed.get('witnesses',[])}
        saved=stored.get('witnesses',{})
        value['changed_witnesses']=sorted(name for name,row in rows.items() if name in saved
            and hexadecimal(saved[name]['after']) and row['state']=='available'
            and row.get('scope_fingerprint')!=saved[name]['after'])
        value['unavailable_witnesses']=sorted(name for name in stored['scope']['witnesses']
            if name not in rows or rows[name]['state']!='available')
    value.update(before=stored['before'],after=stored['after'])
    if observed['state']=='incomplete':
        value['issues'].append('Required current external input coverage is incomplete.')
    elif stored['state']=='incomplete':
        value['issues']+=stored['issues'] or ['Saved external execution coverage is incomplete.']
    elif stored['state']=='stale' or observed['state']!='available' or observed['fingerprint']!=stored['after']:
        value.update(state='stale',issues=['Selected external inputs changed or their required scope was removed.'])
    else:
        value['state']='bound'
    if value.get('changed_witnesses'):
        value['issues'].append('Changed selected witnesses: '+', '.join(value['changed_witnesses']))
    if value.get('unavailable_witnesses'):
        value['issues'].append('Unavailable selected witnesses: '+', '.join(value['unavailable_witnesses']))
    return value


def markdown(value):
    from ..export import _text
    lines=[]
    if value.get('scope'):
        lines.append('Selected witnesses: '+_text(', '.join(value['scope']['witnesses'])))
    lines += ['- '+_text(issue) for issue in value.get('issues',[])]
    return lines
