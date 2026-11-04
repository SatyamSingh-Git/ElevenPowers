"""Propose files that carry the same rule, for a person to certify as a milestone.

Discover-certify-ground, borrowed from NVIDIA Auto-Ontology: this proposes; a
person accepts entries into elevenpowers.milestones.json; only declared rules
reach an agent. The method is the one measured in
results/multistage-v3/discover/README.md: functions in different non-test files,
scored by the rarity-weighted tokens they share, normalised by size.
"""
import ast
from collections import defaultdict
import io
import keyword
import math
from pathlib import Path
import re
import time
import tokenize

from ..config import load as load_config
from ..evidence import SOURCE_SUFFIXES, scan_sources
from ..surface import TEST_NAME
from .definition import load as load_declarations

# Tokens held by more functions than this weigh little and cost quadratic time.
MAX_HOLDERS = 200
# Code this version cannot read; data formats carry no functions to compare.
UNREAD = SOURCE_SUFFIXES - {'.py', '.json', '.yaml', '.yml', '.toml', '.css', '.scss'}
COMMON = set(keyword.kwlist) | {'self', 'cls', 'None', 'True', 'False', 'int', 'str', 'float', 'len', 'dict',
                                'list', 'return', 'value', 'name', 'path', 'row', 'rows'}


def _tokens(source):
    found = set()
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type in (tokenize.NAME, tokenize.STRING, tokenize.NUMBER) and token.string not in COMMON:
                found.add(token.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return found


def _functions(source):
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []
    return [(node.name, _tokens(ast.get_source_segment(source, node) or ''))
            for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _entry(files, functions, shared, command):
    slug = re.sub(r'[^A-Za-z0-9_-]', '-', f'rule-{functions[0]}-{functions[1]}')[:64]
    return {'id': slug, 'description': f"TODO: name the rule both files keep (they share {', '.join(shared[:3])}).",
            'inputs': list(files), 'checks': [{'kind': 'test_suite', 'command': command}] if command else []}


def propose(root, *, limit=50, seconds=30):
    root = Path(root).resolve(strict=True)
    deadline = time.monotonic() + seconds
    scan = scan_sources(root, deadline=deadline)
    issues = list(scan.issues)
    python = [p for p in scan.files if p.endswith('.py') and not TEST_NAME.search(p)]
    unread = [p for p in scan.files if Path(p).suffix in UNREAD and not TEST_NAME.search(p)]
    if unread:
        issues.append(f'{len(unread)} non-Python source files were not examined')
    texts = {}
    for path in python:
        try:
            texts[path] = (root / path).read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            issues.append(f'{path} could not be read')
    held = defaultdict(int)
    for text in texts.values():
        for word in _tokens(text):
            held[word] += 1
    idf = {word: math.log(len(texts) / count) for word, count in held.items()}
    rows = [(path, name, {w for w in words if idf.get(w, 0) > 0})
            for path, text in texts.items() for name, words in _functions(text)]
    weight = [sum(idf[w] for w in words) for _, _, words in rows]
    index = defaultdict(list)
    for i, (_, _, words) in enumerate(rows):
        for word in words:
            index[word].append(i)
    skipped = sum(len(holders) > MAX_HOLDERS for holders in index.values())
    if skipped:
        issues.append(f'{skipped} tokens held by more than {MAX_HOLDERS} functions were skipped')
    shared = defaultdict(float)
    for word, holders in index.items():
        if len(holders) > MAX_HOLDERS:
            continue
        if time.monotonic() >= deadline:
            issues.append('time budget reached; proposals are partial')
            break
        for x, i in enumerate(holders):
            for j in holders[x + 1:]:
                if rows[i][0] != rows[j][0]:
                    shared[i, j] += idf[word]
    declared = load_declarations(root)
    issues += declared['issues']
    together = {frozenset((a, b)) for m in declared['milestones'] for a in m['inputs'] for b in m['inputs'] if a != b}
    best = {}
    for (i, j), total in shared.items():
        files = tuple(sorted((rows[i][0], rows[j][0])))
        if frozenset(files) in together or not weight[i] or not weight[j]:
            continue
        score = total / math.sqrt(weight[i] * weight[j])
        if score > best.get(files, (0,))[0]:
            first, second = (i, j) if rows[i][0] == files[0] else (j, i)
            best[files] = (score, (rows[first][1], rows[second][1]),
                           sorted(rows[i][2] & rows[j][2], key=lambda w: (-idf[w], w))[:5])
    command = load_config(root).command_for('tests')
    if not command:
        issues.append('no declared tests command: add a check to each entry before certifying it')
    ordered = sorted(best.items(), key=lambda item: (-item[1][0], item[0]))[:limit]
    proposals = [{'score': round(score, 4), 'files': list(files), 'functions': list(functions), 'shared': common,
                  'entry': _entry(files, functions, common, command)}
                 for files, (score, functions, common) in ordered]
    return {'schema': 1, 'proposals': proposals,
            'coverage': {'complete': not issues, 'python_files': len(texts), 'functions': len(rows),
                         'not_examined': len(unread), 'issues': issues},
            'limits': ['Proposals are candidates for a person to certify, never findings.',
                       'Shared rare tokens suggest a shared rule; they do not show one.',
                       'Only Python sources are examined in this version.']}
