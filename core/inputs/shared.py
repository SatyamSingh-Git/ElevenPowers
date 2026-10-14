"""Operation-local external phases; source and execution stay independently read."""
from contextvars import ContextVar
from copy import deepcopy
from functools import wraps
from pathlib import Path
import time

_CURRENT=ContextVar('external_input_collection',default=None)


def current(root):
    value=_CURRENT.get()
    return value if value is not None and value['root']==Path(root).resolve() else None


def observation(root,deadline,collector):
    value=current(root)
    if value is None: return collector(root,deadline)
    deadline=min(deadline,value['deadline'])
    if time.monotonic()>=deadline:
        return collector(root,deadline)
    phase=value['phase']
    if phase not in value:
        value[phase]=collector(root,deadline)
    return deepcopy(value[phase])


def closing(root,deadline):
    from .collection import capture
    value=current(root)
    if value is not None: value['phase']='closing'
    return capture(root,deadline)


def operation(function):
    @wraps(function)
    def run(root,*args,**kwargs):
        if current(root) is not None: return function(root,*args,**kwargs)
        timeout=kwargs.get('timeout',120)
        deadline=time.monotonic()+timeout if type(timeout) in (int,float) else time.monotonic()
        value={'root':Path(root).resolve(),'deadline':deadline,'phase':'opening'}
        token=_CURRENT.set(value)
        try:
            return function(root,*args,**kwargs)
        finally:
            _CURRENT.reset(token)
    return run
