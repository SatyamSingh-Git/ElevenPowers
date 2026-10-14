"""Strict portable declarations; no filesystem approval is implied."""
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat

from .access import opened

FILE = 'elevenpowers.inputs.json'
MAX_BYTES = 65536
DEFAULTS = {'files': 2048, 'bytes': 32*1024*1024, 'seconds': 10}


def label(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', value):
        raise ValueError('unsupported input label')
    return value


def stamp(state):
    # Windows ctime is creation time, and real path/descriptor reads can disagree
    # after replacement. Identity, type, links, size and mtime remain comparable.
    common = (state.st_dev, state.st_ino, state.st_mode, state.st_nlink,
              state.st_size, state.st_mtime_ns)
    return common if os.name == 'nt' else (*common, state.st_ctime_ns)


def raw(path, limit=MAX_BYTES, *, optional=False):
    path = Path(path).absolute()
    if path.is_symlink() or path.resolve() != path:
        raise ValueError('linked input state is unsupported')
    try:
        before = path.stat()
    except FileNotFoundError:
        if optional:
            return None
        raise ValueError('input state is unavailable') from None
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > limit:
        raise ValueError('input state type, link or byte limit exceeded')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_BINARY', 0)
    descriptor = opened(path, flags)
    with os.fdopen(descriptor, 'rb') as stream:
        if stamp(os.fstat(stream.fileno())) != stamp(before):
            raise ValueError('input state changed before read')
        data = stream.read(limit+1)
        after = os.fstat(stream.fileno())
    if (len(data) > limit or stamp(after) != stamp(before)
            or path.resolve() != path or stamp(path.stat()) != stamp(before)):
        raise ValueError('input state changed or exceeded read limit')
    return data


def decode(data):
    def pairs(items):
        result = {}
        for name, value in items:
            if name in result:
                raise ValueError('duplicate input state key')
            result[name] = value
        return result
    def invalid(value):
        raise ValueError('non-finite input state value')
    try:
        return json.loads(data, object_pairs_hook=pairs, parse_constant=invalid)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError('malformed input state') from error


def relative(value):
    if (not isinstance(value, str) or not value or len(value) > 4096
            or any(c in value for c in '\\:*?\0') or PurePosixPath(value).is_absolute()
            or PureWindowsPath(value).drive or '..' in value.split('/')
            or PurePosixPath(value).as_posix() != value):
        raise ValueError('input paths must be literal portable relative paths')
    return value


def load(root):
    data = raw(Path(root)/FILE, optional=True)
    if data is None:
        return None
    value = decode(data)
    if (not isinstance(value, dict) or set(value)-{'schema','witnesses','limits','commands'}
            or type(value.get('schema')) is not int or value['schema'] not in (1,2)
            or value['schema']==1 and 'commands' in value
            or not isinstance(value.get('witnesses'), list) or not 1 <= len(value['witnesses']) <= 32):
        raise ValueError('unsupported input declaration')
    seen = set()
    for witness in value['witnesses']:
        if not isinstance(witness, dict) or set(witness) != {'id','root','paths'}:
            raise ValueError('unsupported input witness')
        name = label(witness['id']); label(witness['root'])
        if name in seen:
            raise ValueError('duplicate input witness label')
        seen.add(name)
        paths = witness['paths']
        if (not isinstance(paths, list) or not 1 <= len(paths) <= 32
                or any(relative(p) != p for p in paths) or len(set(paths)) != len(paths)):
            raise ValueError('unsupported or duplicate input paths')
    commands = value.get('commands', [])
    if not isinstance(commands,list) or len(commands)>64:
        raise ValueError('unsupported input command mappings')
    mapped=set()
    from ..redact import scrub
    for item in commands:
        if (not isinstance(item,dict) or set(item)!={'command','witnesses','complete'}
                or not isinstance(item['command'],str) or not item['command'].strip()
                or len(item['command'])>8192 or '\0' in item['command']
                or type(item['complete']) is not bool
                or not isinstance(item['witnesses'],list) or not 1<=len(item['witnesses'])<=32
                or any(not isinstance(w,str) or w not in seen for w in item['witnesses'])
                or len(set(item['witnesses']))!=len(item['witnesses'])
                or item['command'].strip() in mapped):
            raise ValueError('unsupported or ambiguous input command scope')
        mapped.add(item['command'].strip())
        if scrub(item['command'])!=item['command']:
            raise ValueError('redacted command identity cannot qualify an input scope')
    limits = value.get('limits', {})
    if not isinstance(limits, dict) or set(limits)-set(DEFAULTS):
        raise ValueError('unsupported input limits')
    limits = {**DEFAULTS, **limits}
    if (type(limits['files']) is not int or not 1 <= limits['files'] <= 16384
            or type(limits['bytes']) is not int or not 1 <= limits['bytes'] <= 256*1024*1024
            or type(limits['seconds']) not in (int,float) or not 0 <= limits['seconds'] <= 60
            or not math.isfinite(limits['seconds'])):
        raise ValueError('input limits exceed supported finite ranges')
    return {**value, 'limits': limits, '_digest': hashlib.sha256(data).hexdigest()}
