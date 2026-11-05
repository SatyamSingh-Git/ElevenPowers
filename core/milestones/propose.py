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
import json
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
    # ast.get_source_segment splits the whole file again for each function: on sqlalchemy that
    # was 25 of the 30 seconds. This is its split (only \r\n, \r and \n end a line), done once.
    lines = re.findall(r'[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+\Z', source)
    return [(node.name, _tokens(_segment(lines, node)))
            for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _segment(lines, node):
    # Column offsets count UTF-8 bytes, as in ast.get_source_segment.
    first, last = node.lineno - 1, node.end_lineno - 1
    if first == last:
        return lines[first].encode()[node.col_offset:node.end_col_offset].decode()
    return ''.join([lines[first].encode()[node.col_offset:].decode(), *lines[first + 1:last],
                    lines[last].encode()[:node.end_col_offset].decode()])


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
    texts, cut, held = {}, {}, defaultdict(int)
    # Reading and cutting get half the budget, so that pairing has time for what was read.
    reading = deadline - seconds / 2
    for path in python:
        if time.monotonic() >= reading:
            issues.append(f'time budget reached reading; {len(texts)} of {len(python)} Python files examined')
            break
        try:
            texts[path] = (root / path).read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            issues.append(f'{path} could not be read')
            continue
        cut[path] = _functions(texts[path])
        for word in _tokens(texts[path]):
            held[word] += 1
    idf = {word: math.log(len(texts) / count) for word, count in held.items()}
    rows = [(path, name, {w for w in words if idf.get(w, 0) > 0})
            for path in texts for name, words in cut[path]]
    # fsum, not sum: words come in set order, which follows the hash seed, and copies of one rule
    # tie at a score of 1 only if their sums round the same in every process.
    weight = [math.fsum(idf[w] for w in words) for _, _, words in rows]
    index = defaultdict(list)
    for i, (_, _, words) in enumerate(rows):
        for word in words:
            index[word].append(i)
    skipped = sum(len(holders) > MAX_HOLDERS for holders in index.values())
    if skipped:
        issues.append(f'{skipped} tokens held by more than {MAX_HOLDERS} functions were skipped')
    shared = defaultdict(list)
    for word, holders in index.items():
        if len(holders) > MAX_HOLDERS:
            continue
        if time.monotonic() >= deadline:
            issues.append('time budget reached; proposals are partial')
            break
        for x, i in enumerate(holders):
            for j in holders[x + 1:]:
                if rows[i][0] != rows[j][0]:
                    shared[i, j].append(idf[word])
    declared = load_declarations(root)
    issues += declared['issues']
    together = {frozenset((a, b)) for m in declared['milestones'] for a in m['inputs'] for b in m['inputs'] if a != b}
    best = {}
    for (i, j), parts in shared.items():
        files = tuple(sorted((rows[i][0], rows[j][0])))
        if frozenset(files) in together or not weight[i] or not weight[j]:
            continue
        score = math.fsum(parts) / math.sqrt(weight[i] * weight[j])
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
    # Same-named functions recur (`total` and `total`), and the schema refuses a repeated id.
    taken = {m['id'] for m in declared['milestones']}
    for proposal in proposals:
        base, number = proposal['entry']['id'], 1
        while proposal['entry']['id'] in taken:
            number += 1
            proposal['entry']['id'] = f'{base[:60]}-{number}'
        taken.add(proposal['entry']['id'])
    return {'schema': 1, 'proposals': proposals,
            'coverage': {'complete': not issues, 'python_files': len(texts), 'functions': len(rows),
                         'not_examined': len(unread), 'issues': issues},
            'limits': ['Proposals are candidates for a person to certify, never findings.',
                       'Shared rare tokens suggest a shared rule; they do not show one.',
                       'Only Python sources are examined in this version.']}


def markdown(value):
    coverage = value['coverage']
    lines = ['# Proposed rule groups (candidates to certify, not findings)', '',
             'Each pair shares rare words between two functions in different files. If both keep the same rule,',
             'describe it and add the entry to elevenpowers.milestones.json: an agent editing one file is then',
             'told about the other. Reject the rest. Nothing is written for you.', '',
             f"Examined: {coverage['python_files']} Python files, {coverage['functions']} functions; "
             f"{coverage['not_examined']} other source files not examined."]
    lines += ['Gap: ' + issue for issue in coverage['issues']]
    if not value['proposals']:
        lines += ['', 'No pair of files shares rare words.']
    for number, proposal in enumerate(value['proposals'], 1):
        (a, b), (fa, fb) = proposal['files'], proposal['functions']
        entry = json.dumps(proposal['entry'], indent=2).replace('\n', '\n   ')
        lines += ['', f"{number}. {a} ({fa}) and {b} ({fb}), score {proposal['score']}",
                  f"   Shared: {', '.join(proposal['shared'])}", f'   Entry: {entry}']
    return '\n'.join(lines) + '\n'
