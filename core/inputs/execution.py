"""Observe selected inputs around existing owned commands, without launching any."""
import hashlib
import time
import uuid

from .collection import capture
from .native import configuration
from .receipts import attach
from ..hosts.provenance import fingerprint


def begin(root,deadline):
    observed=capture(root,min(deadline,time.monotonic()+10))
    value={'inputs':observed,'attempt':hashlib.sha256(uuid.uuid4().bytes).hexdigest(),
           'configuration':None,'producer':None,'issues':[]}
    if observed['state']!='not_configured':
        try:
            value.update(configuration=configuration(root),producer=fingerprint())
        except (OSError,ValueError):
            value['issues'].append('Owned input configuration or producer inspection was unavailable.')
    return value


def ready(value):
    return value['inputs']['state'] in {'available','not_configured'} and not value['issues']


def provisional(records,value):
    if value['inputs']['state']=='not_configured': return
    attach(records,value['inputs'],{'state':'incomplete','fingerprint':None},value['attempt'],value['issues'])


def finish(root,deadline,value,records,issues=()):
    observed=capture(root,min(deadline,time.monotonic()+10))
    gaps=list(value['issues'])+list(issues)
    if value['inputs']['state']!='not_configured' or observed['state']!='not_configured':
        try:
            if value['configuration']!=configuration(root) or value['producer']!=fingerprint():
                gaps.append('Owned command configuration or producer changed during execution.')
        except (OSError,ValueError):
            gaps.append('Owned final configuration or producer inspection was unavailable.')
    attach(records,value['inputs'],observed,value['attempt'],gaps)
    value['final_issues']=gaps
    return observed


def from_witness(value):
    if value is None: return {'state':'incomplete','fingerprint':None}
    selected=value.get('external_inputs_fingerprint')
    return {'state':'available' if selected else 'not_configured','fingerprint':selected}
