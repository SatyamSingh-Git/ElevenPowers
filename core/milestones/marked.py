"""Rules a person marked in the code with Google's IfThisThenThat comments.

    # LINT.IfChange(upload_limit)
    MAX_UPLOAD_SIZE_MB = 50
    # LINT.ThenChange(//docs/api.md:upload_limit)

The convention and its reading follow ifttt-lint (github.com/simonepri/ifttt-lint, MIT):
a directive alone on its comment line, no nesting, `//` from the project root. It
checks the pairs in CI; here they reach the agent, before its edit and at its end.
"""
import posixpath
import re
from pathlib import Path
import subprocess

MAX_BYTES = 1024 * 1024
MAX_BLOCKS = 64
DIRECTIVE = re.compile(r'LINT\.(?P<kind>IfChange|ThenChange)(?:\((?P<args>[^()]*)(?P<close>\))?)?')
CONTINUED = re.compile(r'(?P<args>[^()]*?)(?P<close>\))?')
LABEL = re.compile(r'[A-Za-z][A-Za-z0-9_.-]*')
FENCE = re.compile(r'(```|~~~)')
WRAPPED = (('<!--', '-->'), ('/*', '*/'))
LEADING = ('#', '//', '--', ';', '%')


def present(root):
    """Does any tracked or untracked file hold a `LINT.ThenChange`? Git-only, like the shell path it gates."""
    from ..process import run
    try:
        done = run(['git', 'grep', '-q', '--untracked', '-F', '-e', 'LINT.ThenChange'], cwd=root, timeout=10, shell=False)
    except (OSError, subprocess.SubprocessError):
        return False
    return done.returncode == 0


def read(root, path, text=None):
    """The marked blocks in one project file, and what could not be read as one."""
    from .definition import safe_path
    root = Path(root)
    if path.endswith(('.patch', '.diff')):
        # A patch quotes another file's lines, directives included.
        return [], []
    try:
        full = safe_path(root, path)
        if text is None and full.stat().st_size > MAX_BYTES:
            return [], [f'{path}: larger than 1 MiB; its marked rules were not read']
        text = full.read_text(encoding='utf-8', errors='replace') if text is None else text
    except (OSError, ValueError):
        return [], []
    if 'LINT.' not in text:
        return [], []
    blocks, issues = _parse(text, path)
    labels = {b['label'] for b in blocks if b['label']}
    for block in blocks:
        block['targets'] = [_target(root, path, spec, labels) for spec in block['targets']]
    return blocks[:MAX_BLOCKS], issues


def _parse(text, path):
    blocks, issues, open_at, label, fenced = [], [], None, None, False
    lines = text.splitlines()
    number = 0
    while number < len(lines):
        line = lines[number].strip()
        number += 1
        if path.endswith(('.md', '.markdown')) and FENCE.match(line):
            fenced = not fenced
            continue
        found = None if fenced else DIRECTIVE.fullmatch(_comment(line) or '')
        if not found:
            continue
        if found['kind'] == 'IfChange':
            if found['args'] is not None and (not found['close'] or not LABEL.fullmatch(found['args'].strip())):
                continue
            if open_at is not None:
                issues.append(f'{path}:{number}: LINT.IfChange inside an open block; nesting is not supported')
            open_at, label = number, found['args'].strip() if found['args'] else None
            continue
        if found['args'] is None:
            continue
        start, args = number, found['args']
        while not found['close']:
            inner = _comment(lines[number].strip()) if number < len(lines) else None
            found = CONTINUED.fullmatch(inner) if inner is not None else None
            if not found:
                issues.append(f'{path}:{start}: LINT.ThenChange target list is never closed')
                break
            number += 1
            args += ',' + found['args']
        else:
            if open_at is None:
                issues.append(f'{path}:{start}: LINT.ThenChange with no open LINT.IfChange')
                continue
            blocks.append({'path': path, 'label': label, 'start': open_at, 'end': number,
                           'targets': [spec.strip() for spec in args.split(',') if spec.strip()]})
        open_at = None
    if open_at is not None:
        issues.append(f'{path}:{open_at}: LINT.IfChange is never closed by a LINT.ThenChange')
    return blocks, issues


def listing(root, limit=2000):
    """Every marked rule in the project, with each target checked to exist, for a person to read."""
    from ..process import run
    rules, issues = [], []
    try:
        done = run(['git', 'grep', '-l', '-z', '--untracked', '-F', '-e', 'LINT.IfChange', '-e', 'LINT.ThenChange'],
                   cwd=root, timeout=30, shell=False)
    except (OSError, subprocess.SubprocessError):
        done = None
    if done is None or done.returncode not in (0, 1):
        return {'rules': [], 'issues': ['marked rules are found with git grep, which could not run here']}
    paths = sorted(p for p in done.stdout.split('\0') if p)
    if len(paths) > limit:
        issues.append(f'{len(paths)} files hold directives; the first {limit} were read')
    for path in paths[:limit]:
        blocks, found = read(root, path)
        issues += found
        for block in blocks:
            for target in block['targets']:
                target['missing'] = None if target['found'] else 'file' if target['path'] != path else 'label'
                if target['found'] and target['label'] and target['path'] != path:
                    target['found'] = any(b['label'] == target['label'] for b in read(root, target['path'])[0])
                    target['missing'] = None if target['found'] else 'label'
            rules.append(block)
    return {'rules': rules, 'issues': issues}


def listing_text(value):
    lines = ['# Marked rules', '', f"{len(value['rules'])} marked rules "
             f"in {len({r['path'] for r in value['rules']})} files.", '']
    for rule in value['rules']:
        shown = ', '.join(t['spec'] + ' (not found)' if t['missing'] == 'file' else
                          t['path'] + (f":{t['label']}" if t['label'] else '')
                          + (' (label not found)' if t['missing'] == 'label' else '')
                          for t in rule['targets']) or 'no targets: a label other rules name'
        lines.append(f"- {rule['label'] or 'unnamed'}: {rule['path']} lines {rule['start']}-{rule['end']} -> {shown}")
    if value['issues']:
        lines += ['', 'Issues:'] + [f'- {issue}' for issue in value['issues']]
    return '\n'.join(lines) + '\n'


def left_behind(root, touched, base):
    """Marked blocks this task changed while a target they name did not change."""
    said, changes = [], {}

    def changed(path, block=None):
        if not base:
            return path in touched
        if path not in changes:
            changes[path] = _changes(root, base, path)
        lines, after = changes[path]
        if block is None:
            return bool(lines or after)
        return (any(block['start'] < line < block['end'] for line in lines)
                or any(block['start'] <= line < block['end'] for line in after))

    for path in touched:
        blocks = read(root, path)[0]
        for block in blocks:
            if not changed(path, block):
                continue
            for target in block['targets']:
                if not target['found']:
                    continue
                labelled = [b for b in (blocks if target['path'] == path else read(root, target['path'])[0])
                            if target['label'] and b['label'] == target['label']]
                if not changed(target['path'], labelled[0] if labelled else None):
                    name = target['path'] + (f":{target['label']}" if target['label'] else '')
                    said.append(f"marked rule {block['label'] or 'unnamed'} ({path} lines {block['start']}-{block['end']}): "
                                f'changed, not {name}')
    return said


HUNK = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', re.M)


def _changes(root, base, path):
    """New-side lines this task changed in `path`, and the lines a deletion follows."""
    from ..process import run
    try:
        diff = run(['git', 'diff', '-U0', base, '--', path], cwd=root, timeout=10, shell=False)
        tracked = run(['git', 'ls-files', '--error-unmatch', '--', path], cwd=root, timeout=10, shell=False)
    except (OSError, subprocess.SubprocessError):
        return set(), set()
    if tracked.returncode:
        # Untracked: the whole file is what this task added.
        text = (Path(root) / path).read_text(encoding='utf-8', errors='replace') if (Path(root) / path).is_file() else ''
        return set(range(1, len(text.splitlines()) + 1)), set()
    lines, after = set(), set()
    for start, count in HUNK.findall(diff.stdout if diff.returncode == 0 else ''):
        count = 1 if count == '' else int(count)
        if count:
            lines.update(range(int(start), int(start) + count))
        else:
            after.add(int(start))
    return lines, after


def _comment(line):
    """The text of a comment line, or None. A closing `-->` or `*/` must match its opener."""
    for opener, closer in WRAPPED:
        if line.startswith(opener) and line.endswith(closer) and len(line) >= len(opener) + len(closer):
            return line[len(opener):-len(closer)].strip()
    for opener in LEADING:
        if line.startswith(opener):
            return line[len(opener):].strip()
    return None


def _target(root, path, spec, labels):
    where, _, label = spec.rpartition(':')
    if not where and not label:
        where, label = spec, ''
    if label and not LABEL.fullmatch(label):
        where, label = spec, ''
    if not where:
        return {'spec': spec, 'path': path, 'label': label, 'found': label in labels}
    if where.startswith('//'):
        candidates = [where[2:]]
    else:
        candidates = [posixpath.join(posixpath.dirname(path), where), where]
    for candidate in candidates:
        candidate = posixpath.normpath(candidate)
        if candidate.startswith('../') or candidate == '..' or posixpath.isabs(candidate):
            continue
        if (root / candidate).is_file():
            return {'spec': spec, 'path': candidate, 'label': label or None, 'found': True}
    # Only a `//` path names one place; a bare one found under neither reading is not guessed at.
    unique = posixpath.normpath(candidates[0]) if len(candidates) == 1 else None
    return {'spec': spec, 'path': unique if unique and not unique.startswith('..') else None,
            'label': label or None, 'found': False}
