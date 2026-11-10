"""Path-scoped rules other agents already have, read as each agent writes them.

Four formats, read-only: Claude Code's `.claude/rules` (`paths:`), Cursor's `.cursor/rules/*.mdc`
(`globs:`), Copilot's `.github/instructions/*.instructions.md` (`applyTo:`), and an `AGENTS.md` in a
subfolder, which scopes to that folder. Glob semantics are CPython 3.13's `glob.translate` with
`recursive=True`, vendored because 3.11 lacks it; Claude Code alone lets a pattern without a slash
match at any depth ("`/*.md` (base directory only)").
docs/superpowers/specs/2026-11-10-rules-from-every-agent-design.md
"""
import os
from pathlib import Path
import re

from ..evidence import IGNORED_DIRS
from ..process import run

LIMIT = 600
MOST = 2
SOURCES = (('claude', '.claude/rules', '.md', 'paths', True),
           ('cursor', '.cursor/rules', '.mdc', 'globs', False),
           ('copilot', '.github/instructions', '.instructions.md', 'applyTo', False))
# What each host loads itself when it edits a matching file; skipped on the Edit brief only.
NATIVE = {'claude': {'claude'}, 'cursor': {'cursor', 'agents'}, 'copilot': {'copilot', 'agents'}}


def _braces(pattern):
    match = re.search(r'\{([^{}]*)\}', pattern)
    if not match:
        return [pattern]
    return [expanded for part in match.group(1).split(',')
            for expanded in _braces(pattern[:match.start()] + part + pattern[match.end():])]


def _segment(text):
    out, i = '', 0
    while i < len(text):
        char = text[i]
        if char == '*':
            out += '[^/]*'
        elif char == '?':
            out += '[^/]'
        elif char == '[':
            end = text.find(']', i + 2 if text[i + 1:i + 2] in ('!', ']') else i + 1)
            if end < 0:
                raise ValueError(text)
            inner = text[i + 1:end]
            out += '[' + ('^' + inner[1:] if inner.startswith('!') else inner).replace('\\', '\\\\') + ']'
            i = end
        else:
            out += re.escape(char)
        i += 1
    return out


def translate(pattern, floating):
    """A compiled regex over `/`-separated relative paths, or None for an invalid bracket."""
    alternatives = []
    try:
        for expanded in _braces(pattern):
            anchored = expanded.startswith('/')
            expanded = expanded.lstrip('/')
            if floating and not anchored and '/' not in expanded:
                expanded = '**/' + expanded
            parts = expanded.split('/')
            regex = ''
            for n, part in enumerate(parts):
                last = n == len(parts) - 1
                if part == '**':
                    regex += '.*' if last else '(?:[^/]+/)*'
                else:
                    regex += _segment(part) + ('' if last else '/')
            alternatives.append(regex)
    except ValueError:
        return None
    return re.compile('(?:' + '|'.join(alternatives) + ')')


def frontmatter(text):
    """(fields, body) of a `---` block, or None when it is not one this reader understands."""
    lines = text.lstrip('\ufeff').replace('\r\n', '\n').split('\n')
    if not lines or lines[0].strip() != '---' or '---' not in [line.strip() for line in lines[1:]]:
        return None
    end = 1 + [line.strip() for line in lines[1:]].index('---')
    fields, key = {}, None
    for line in lines[1:end]:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if stripped.startswith('- ') and key is not None:
            fields.setdefault(key, [])
            if not isinstance(fields[key], list):
                return None
            fields[key].append(stripped[2:].strip().strip('"\''))
            continue
        name, sep, value = stripped.partition(':')
        if not sep or not name.strip() or ' ' in name.strip():
            return None
        key, value = name.strip(), value.strip()
        if value.startswith('[') and value.endswith(']'):
            fields[key] = [v.strip().strip('"\'') for v in value[1:-1].split(',') if v.strip()]
        elif value:
            fields[key] = value.strip('"\'')
    return fields, '\n'.join(lines[end + 1:]).strip()


def _agents_files(root):
    """Every AGENTS.md: from git when it can answer (74 ms here, against 1.5 s for a walk of this
    repository on every first edit), tracked or untracked but not ignored; otherwise a walk."""
    done = run(['git', 'ls-files', '-co', '--exclude-standard', '-z', '--', ':(glob)**/AGENTS.md'],
               cwd=root, timeout=10, shell=False)
    if done.returncode == 0:
        return [root / name for name in done.stdout.split('\0') if name]
    found = []
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        if 'AGENTS.md' in files:
            found.append(Path(folder) / 'AGENTS.md')
    return found


def read(root):
    """Every scoped rule in the project, and the files that could not be read as one."""
    root = Path(root)
    rules, issues = [], []
    for fmt, folder, suffix, key, floating in SOURCES:
        base = root / folder
        for path in sorted(base.rglob('*' + suffix)) if base.is_dir() else []:
            source = path.relative_to(root).as_posix()
            try:
                parsed = frontmatter(path.read_text(encoding='utf-8'))
            except (OSError, UnicodeError):
                parsed = None
            if parsed is None:
                issues.append(f'{source}: front matter could not be read; not delivered')
                continue
            fields, body = parsed
            if fmt == 'cursor' and str(fields.get('alwaysApply', '')).lower() == 'true':
                continue
            raw = fields.get(key, [])
            patterns = [p.strip() for p in (raw.split(',') if isinstance(raw, str) else raw) if p.strip()]
            valid = [p for p in patterns if translate(p, floating) is not None]
            issues += [f'{source}: pattern {p} is not a valid glob; it matches nothing' for p in patterns if p not in valid]
            if valid and body:
                rules.append({'source': source, 'format': fmt, 'patterns': valid, 'body': body})
    for path in sorted(_agents_files(root)):
        if path.parent != root:
            folder = path.parent.relative_to(root).as_posix()
            try:
                body = path.read_text(encoding='utf-8').strip()
            except (OSError, UnicodeError):
                issues.append(f'{folder}/AGENTS.md could not be read; not delivered')
                continue
            if body:
                rules.append({'source': f'{folder}/AGENTS.md', 'format': 'agents',
                              'patterns': [f'{folder}/**'], 'body': body})
    return rules, issues


def lines_for(root, path, platform, kind, cwd=''):
    """The rules for one file the agent is changing, as note lines, skipping what the host loads."""
    path = path.replace('\\', '/').lstrip('/')
    cwd = cwd.replace('\\', '/').strip('/')
    skipped = NATIVE.get(platform, set()) if kind == 'edit' else set()
    found, closest = [], None
    for rule in read(root)[0]:
        if rule['format'] in skipped or not any(
                translate(p, rule['format'] == 'claude').fullmatch(path) for p in rule['patterns']):
            continue
        if rule['format'] == 'agents':
            folder = rule['source'].rsplit('/', 1)[0]
            if kind == 'edit' and platform == 'codex' and (cwd == folder or cwd.startswith(folder + '/')):
                continue
            if closest is None or len(folder) > len(closest['source'].rsplit('/', 1)[0]):
                closest = rule
            continue
        found.append(rule)
    found += [closest] if closest else []
    lines = []
    for rule in sorted(found, key=lambda r: r['source'])[:MOST]:
        text = rule['body']
        if len(text) > LIMIT:
            text = text[:LIMIT] + f"… (rest in {rule['source']})"
        lines.append(f"Project rule from {rule['source']} (applies to {', '.join(rule['patterns'])}): {text}")
    return lines
