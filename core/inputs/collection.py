"""Bounded fresh local-byte observations; unknown coverage cannot qualify reuse."""
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import time

from ..redact import scrub_values
from . import definition, bindings

LIMITS = [
    'Selected approved local bytes only; other dependencies, tools and remote services remain unobserved.',
    'Unsigned local declarations and approval require trust in the caller and project state.',
    'Before/after reads are not atomic and cannot detect intervening reverted changes.',
    'Filesystem calls are cooperative; incomplete coverage cannot qualify reuse.',
    'No project checks, package imports, installations or model/network probes run during inspection.',
]


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=True,sort_keys=True,
                                    separators=(',',':'),allow_nan=False).encode()).hexdigest()


def issue(error):
    if isinstance(error,ValueError):
        return 'ValueError: '+str(error)[:192]
    return type(error).__name__+': selected input inspection unavailable'


class Scan:
    def __init__(self,limits,deadline):
        self.limits = limits
        self.deadline = min(deadline,time.monotonic()+limits['seconds'])
        self.counts = {'files':0,'bytes':0,'entries':0}
        self.files, self.directories, self.roots = {},{},{}

    def check(self):
        if time.monotonic() >= self.deadline:
            raise TimeoutError('input collection deadline reached')

    def inventory(self,path):
        self.check()
        before = definition.stamp(path.stat())
        found = []
        with os.scandir(path) as entries:
            for entry in entries:
                self.check()
                self.counts['entries'] += 1
                if self.counts['entries'] > self.limits['files']*2:
                    raise ValueError('input directory entry budget exceeded')
                found.append((entry.name,definition.stamp(entry.stat(follow_symlinks=False))))
        if path.resolve() != path or before != definition.stamp(path.stat()):
            raise ValueError('input directory changed during enumeration')
        return before,sorted(found)

    def walk(self,approved,path,depth=0):
        self.check()
        if depth > 32:
            raise ValueError('input directory depth exceeded')
        if (not path.is_relative_to(approved) or path.is_symlink() or path.resolve() != path):
            raise ValueError('selected input is linked or outside approved root')
        before = path.stat()
        if stat.S_ISDIR(before.st_mode):
            if path not in self.directories:
                self.directories[path] = self.inventory(path)
            result = [path]
            for name,_ in self.directories[path][1]:
                result.extend(self.walk(approved,path/name,depth+1))
            return result
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError('selected input type or hard links are unsupported')
        if path not in self.files:
            if self.counts['files'] >= self.limits['files']:
                raise ValueError('input file budget exceeded')
            data = definition.raw(path,self.limits['bytes']-self.counts['bytes'])
            self.check()
            self.counts['files'] += 1
            self.counts['bytes'] += len(data)
            self.files[path] = (hashlib.sha256(data).hexdigest(),len(data),definition.stamp(before))
        return [path]

    def finish(self):
        for path,(_,_,before) in self.files.items():
            self.check()
            if path.resolve() != path or definition.stamp(path.stat()) != before:
                raise ValueError('selected input changed after reading')
        for path,before in self.directories.items():
            if self.inventory(path) != before:
                raise ValueError('input directory inventory changed')
        for path,before in self.roots.items():
            self.check()
            if path.resolve() != path or definition.stamp(path.stat()) != before:
                raise ValueError('approved input root changed')


def capture(root,deadline):
    from .shared import observation
    return observation(root,deadline,_capture)


def _capture(root,deadline):
    root = Path(root).resolve(strict=True)
    value = {'schema':1,'state':'not_configured','fingerprint':None,'witnesses':[],
             'counts':{'files':0,'bytes':0,'entries':0},'issues':[],'limits':LIMITS}
    try:
        declaration = definition.load(root)
        if declaration is None:
            return value
        value['state'] = 'incomplete'
        value['witnesses'] = [{'id':w['id'],'root':w['root'],'state':'incomplete',
                              'fingerprint':None,'files':0,'issues':[]} for w in declaration['witnesses']]
        if not math.isfinite(deadline):
            raise ValueError('input collection requires finite deadline')
        scan = Scan(declaration['limits'],deadline)
        value['budgets'] = {**declaration['limits'],'entries':declaration['limits']['files']*2,'depth':32}
        scan.check()
        approval = bindings.load(root,declaration,scan.deadline)
        for witness,row in zip(declaration['witnesses'],value['witnesses']):
            try:
                approved = bindings.directory(root,approval['roots'][witness['root']])
                scan.roots.setdefault(approved,definition.stamp(approved.stat()))
                selected = set()
                for relative in witness['paths']:
                    selected.update(scan.walk(approved,approved/relative))
                files = {p for p in selected if p in scan.files}
                if not files:
                    raise ValueError('selected input scope is empty; no file bytes observed')
                records = {p.relative_to(approved).as_posix():
                           ['file',*scan.files[p][:2]] if p in files else ['directory']
                           for p in selected}
                row.update(state='available',files=len(files),
                           fingerprint=digest([witness,records]))
                if declaration['schema']==2:
                    row['scope_fingerprint']=digest([witness,records,approval['roots'][witness['root']],
                                                     declaration['limits']])
            except (OSError,ValueError,TimeoutError,subprocess.SubprocessError) as error:
                row['issues'].append(issue(error))
                value['issues'].append(witness['id']+': '+issue(error))
        scan.finish()
        scan.check()
        if (definition.load(root) != declaration or
                bindings.load(root,declaration,scan.deadline) != approval):
            raise ValueError('input declaration or local approval changed during collection')
        value['counts'] = dict(scan.counts)
        if declaration['schema']==2:
            from .scopes import command_key
            value['scopes']=[{'command':command_key(c['command']), 'witnesses':sorted(c['witnesses'])}
                             for c in declaration.get('commands',[]) if c['complete']]
        if not value['issues'] and all(w['state']=='available' for w in value['witnesses']):
            value.update(state='available',fingerprint=digest([declaration['_digest'],
                         approval['_digest'],[(w['id'],w['fingerprint']) for w in value['witnesses']]]))
    except (OSError,ValueError,TimeoutError,TypeError,subprocess.SubprocessError) as error:
        value['state'] = 'incomplete'
        value['fingerprint'] = None
        value['issues'].append(issue(error))
        for row in value['witnesses']:
            row.update(state='incomplete',fingerprint=None)
            row.pop('scope_fingerprint',None)
        if 'scan' in locals():
            value['counts'] = dict(scan.counts)
    return scrub_values(value)


def markdown(value):
    from ..export import _text
    lines = ['## Declared external inputs', '',
             'Current collection: '+_text(value['state']),
             'Selected-input fingerprint: '+_text(value['fingerprint'] or 'unavailable'),
             'Source-only receipt facts remain separate; current collection does not imply a matching saved execution.',
             'Only declared approved bytes are inspected; the complete environment remains unobserved.', '',
             '| Witness | Root label | Collection | Files |', '|---|---|---|---|']
    for row in value['witnesses']:
        lines.append('| '+' | '.join(_text(v) for v in (row['id'],row['root'],row['state'],row['files']))+' |')
    lines += ['', *['- '+_text(i) for i in value['issues']+value['limits']]]
    return '\n'.join(lines)+'\n'
