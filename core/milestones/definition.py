"""Strict, bounded project declarations; parsing never executes a check."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import time

FILE = 'elevenpowers.milestones.json'
MAX_BYTES = 128 * 1024
KINDS = {'test_suite', 'build', 'typecheck', 'lint', 'benchmark'}


def safe_path(root, value):
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError('input must be a nonempty normalized relative path')
    path = PurePosixPath(value)
    if ('\\' in value or ':' in value or path.is_absolute() or str(path) != value
            or '..' in path.parts or any(p in {'.git', '.elevenpowers'} for p in path.parts)):
        raise ValueError('unsafe milestone input path')
    root = Path(root).resolve()
    full = root / value
    if (any((root / str(p)).is_symlink() for p in (path, *path.parents))
            or any((root / str(p) / '.git').exists() for p in path.parents if str(p) != '.')
            or not full.resolve().is_relative_to(root)):
        raise ValueError('linked or nested-repository milestone input')
    if full.exists() and not full.is_file():
        raise ValueError('milestone input must be an ordinary file')
    return full


def configured(root):
    path = Path(root) / FILE
    return path.exists() or path.is_symlink()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON field in milestone declaration')
        result[key] = value
    return result


def _text(value, name, maximum=4096):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f'invalid milestone {name}')


def _array(value, name, maximum):
    if not isinstance(value, list) or not 1 <= len(value) <= maximum:
        raise ValueError(f'invalid milestone {name} count (1-{maximum})')


def load(root, *, deadline=None):
    result = {'configured': configured(root), 'fingerprint': '', 'milestones': [], 'issues': []}
    if not result['configured']:
        return result
    try:
        if deadline is not None and time.monotonic() >= deadline:
            raise ValueError('milestone declaration deadline reached')
        path = safe_path(root, FILE)
        with path.open('rb') as stream:
            data = stream.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError('milestone declaration exceeds 128 KiB')
        result['fingerprint'] = hashlib.sha256(data).hexdigest()
        value = json.loads(data.decode('utf-8'), object_pairs_hook=_pairs)
        if (not isinstance(value, dict) or set(value) != {'schema', 'milestones'}
                or type(value['schema']) is not int or value['schema'] != 1):
            raise ValueError('expected milestone declaration schema 1 with no unknown fields')
        _array(value['milestones'], 'definitions', 64)
        ids = set()
        for item in value['milestones']:
            if not isinstance(item, dict) or set(item) != {'id', 'description', 'inputs', 'checks'}:
                raise ValueError('invalid milestone fields')
            _text(item['id'], 'id', 64)
            if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', item['id']) or item['id'] in ids:
                raise ValueError('invalid or duplicate milestone id')
            ids.add(item['id'])
            _text(item['description'], 'description')
            _array(item['inputs'], 'inputs', 128)
            for name in item['inputs']:
                safe_path(root, name)
            if len(set(item['inputs'])) != len(item['inputs']):
                raise ValueError('duplicate milestone input')
            _array(item['checks'], 'checks', 16)
            checks = set()
            for check in item['checks']:
                if (not isinstance(check, dict) or set(check) != {'kind', 'command'}
                        or not isinstance(check['kind'], str) or check['kind'] not in KINDS):
                    raise ValueError('invalid aggregate milestone check')
                _text(check['command'], 'command')
                if check['command'] != check['command'].strip():
                    raise ValueError('check command must preserve a normalized exact identity')
                key = check['kind'], check['command']
                if key in checks:
                    raise ValueError('duplicate milestone check')
                checks.add(key)
        result['milestones'] = value['milestones']
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError) as error:
        result['issues'].append(f'{type(error).__name__}: milestone declarations unavailable or invalid: {error}')
    return result


def add_rule(root, a, b, why=''):
    """Declare that two files keep one rule, worded as the instruction that was measured to be
    followed (5 of 60 dependents lost against 23 of 60 for a description,
    results/rule-mandate-confirm). Returns the entry written."""
    from ..config import load as load_config
    root = Path(root)
    if a == b:
        raise ValueError('a rule needs two different files')
    for name in (a, b):
        if not safe_path(root, name).is_file():
            raise ValueError(f'no such file: {name}')
    command = load_config(root).command_for('tests')
    if not command:
        raise ValueError('no tests command: declare one in .elevenpowers/config.json; a rule needs a check')
    declared = load(root)
    if declared['issues']:
        raise ValueError(f"{FILE} cannot be read: {'; '.join(declared['issues'])}")
    if any({a, b} <= set(m['inputs']) for m in declared['milestones']):
        raise ValueError(f'{a} and {b} are already declared together')
    base = re.sub(r'[^A-Za-z0-9_-]', '-', f'rule-{PurePosixPath(a).stem}-{PurePosixPath(b).stem}')[:60]
    taken, rule_id, number = {m['id'] for m in declared['milestones']}, base, 1
    while rule_id in taken:
        number += 1
        rule_id = f'{base}-{number}'
    entry = {'id': rule_id,
             'description': f'`{a}` and `{b}` must stay consistent: change both in the same task.'
                            + (f' {why.strip()}' if why.strip() else ''),
             'inputs': [a, b], 'checks': [{'kind': 'test_suite', 'command': command}]}
    path = root / FILE
    before = path.read_text(encoding='utf-8') if path.exists() else None
    value = json.loads(before) if before else {'schema': 1, 'milestones': []}
    value['milestones'].append(entry)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    issues = load(root)['issues']
    if issues:
        if before is None:
            path.unlink()
        else:
            path.write_text(before, encoding='utf-8')
        raise ValueError(f"the rule was not written: {'; '.join(issues)}")
    return entry


def rules_naming(root, path, platform='claude', kind='edit', cwd=''):
    """Rules a person declared or marked that keep `path` in step with other files, then the rules other
    agents' files scope to it that this host would not load itself: the rule note."""
    from .marked import read
    from .scoped import lines_for
    lines = []
    for item in load(root)['milestones'] if configured(root) else []:
        others = [p for p in item['inputs'] if p != path]
        if path in item['inputs'] and others:
            shown = ', '.join(others[:4]) + (f' (+{len(others) - 4} more)' if len(others) > 4 else '')
            description = ' '.join(item['description'].split())[:200]
            lines.append(f"Declared rule {item['id']} ({description}) is also kept in {shown}. "
                         'Change them together, or say why one should differ.')
    for block in read(root, path)[0]:
        targets = [t for t in block['targets'] if t['found']]
        if targets:
            shown = ', '.join(t['path'] + (f":{t['label']}" if t['label'] else '') for t in targets[:4])
            lines.append(f"Marked rule {block['label'] or 'unnamed'} ({path} lines {block['start']}-{block['end']}) "
                         f'is also kept in {shown}. Change them together, or say why one should differ.')
    return '\n'.join(lines[:3] + lines_for(root, path, platform, kind, cwd))



def partly_changed(root, touched, base=''):
    """Declared or marked multi-file rules this task changed in some files and not the others."""
    from .marked import left_behind
    said = []
    for item in load(root)['milestones'] if configured(root) else []:
        changed = [p for p in item['inputs'] if p in touched]
        unchanged = [p for p in item['inputs'] if p not in touched]
        if changed and unchanged:
            said.append(f"declared rule {item['id']}: changed {', '.join(changed[:4])}, "
                        f"not {', '.join(unchanged[:4])}")
    return (said + left_behind(root, touched, base))[:5]
