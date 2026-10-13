"""Optional execution observations; current reads cannot invent old provenance."""
import re
import time
from pathlib import Path

from .collection import capture

KEYS={'schema','state','before','after','attempt','issues'}


def hexadecimal(value):
    return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None


def valid(value):
    if (not isinstance(value,dict) or set(value)!=KEYS or type(value['schema']) is not int
            or value['schema']!=1 or not isinstance(value['state'],str)
            or value['state'] not in {'bound','stale','incomplete'}
            or any(v is not None and not hexadecimal(v) for v in (value['before'],value['after']))
            or not (value['attempt']=='' or hexadecimal(value['attempt']))
            or not isinstance(value['issues'],list) or len(value['issues'])>16
            or any(not isinstance(i,str) or len(i)>192 for i in value['issues'])):
        return False
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
    return {'schema':1,'state':state,'before':first,'after':last,'attempt':attempt,'issues':gaps[:16]}


def attach(records,before,after,attempt,issues=()):
    value=metadata(before,after,attempt,issues)
    for record in records:
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
    value.update(before=stored['before'],after=stored['after'])
    if observed['state']=='incomplete':
        value['issues'].append('Required current external input coverage is incomplete.')
    elif stored['state']=='incomplete':
        value['issues']+=stored['issues'] or ['Saved external execution coverage is incomplete.']
    elif stored['state']=='stale' or observed['state']!='available' or observed['fingerprint']!=stored['after']:
        value.update(state='stale',issues=['Selected external inputs changed or their required scope was removed.'])
    else:
        value['state']='bound'
    return value
