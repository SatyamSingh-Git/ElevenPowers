"""Is a declared quiet dependent really quiet? Two checks a v3 rehearsal runs without a model.

Named: the stage's changed names are the definitions its reference diff touches,
the module-level names it reassigns, and identifiers or string literals it
removes outright. A dependent whose file mentions none of them, as a whole word
in its raw text, is not found by searching for what changed. Suite: the project's
own tests still pass with the dependent left behind.
"""
import ast
import builtins
import io
import keyword
import os
from pathlib import Path
import re
import subprocess
import sys
import tokenize

from core.process import run

HUNK = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@')
SHORTEST_LITERAL = 3


def _files(diff):
    """Per file: removed old line numbers, insertions as (old line they follow, indent), removed and added text."""
    files, current, old, run = {}, None, 0, None
    for line in diff.splitlines():
        if not line.startswith('+') or line.startswith('+++ '):
            run = None
        if line.startswith('diff --git '):
            current = line.split(' b/', 1)[1]
            files[current] = (set(), [], [], [])
        elif current is None or line.startswith(('--- ', '+++ ')):
            continue
        elif match := HUNK.match(line):
            # `-L,0` inserts after line L; otherwise L is the first old line the hunk reads.
            old = int(match.group(1)) + (match.group(2) == '0')
        elif line.startswith('-'):
            files[current][0].add(old)
            files[current][2].append(line[1:])
            old += 1
        elif line.startswith('+'):
            text = line[1:]
            files[current][3].append(text)
            # A run of added lines belongs wherever its first non-blank line starts.
            if run is None:
                files[current][1].append([old - 1, None])
                run = files[current][1][-1]
            if run[1] is None and text.strip():
                run[1] = len(text) - len(text.lstrip())
        elif line.startswith(' '):
            old += 1
    return files


def _tokens(lines):
    found = set()
    for line in lines:
        try:
            for token in tokenize.generate_tokens(io.StringIO(line + '\n').readline):
                if (token.type == tokenize.NAME and not keyword.iskeyword(token.string)
                        and not hasattr(builtins, token.string)):
                    found.add(token.string)
                elif token.type == tokenize.STRING:
                    try:
                        value = ast.literal_eval(token.string)
                    except (ValueError, SyntaxError):
                        continue
                    if isinstance(value, str) and len(value) >= SHORTEST_LITERAL:
                        found.add(value)
        except (tokenize.TokenError, IndentationError, SyntaxError):
            continue
    return found


def _innermost(module, inside):
    found = None
    for node in ast.walk(module):
        if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and inside(node)
                and (found is None or node.lineno >= found.lineno)):
            found = node
    return found


def _definitions(source, removed, inserted):
    """The innermost def or class each change lands in, and module names reassigned on a removed line."""
    try:
        module = ast.parse(source)
    except SyntaxError:
        return set()
    found = [_innermost(module, lambda node, line=line: node.lineno <= line <= node.end_lineno) for line in removed]
    # A line added after a body's last line belongs to it only if indented inside it; a new
    # function appended below an old one changes nothing about the old one.
    found += [_innermost(module, lambda node, after=after, indent=indent: node.lineno <= after < node.end_lineno
                         or (after == node.end_lineno and indent > node.col_offset))
              for after, indent in inserted if indent is not None]
    names = {node.name for node in found if node is not None}
    for node in module.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and any(node.lineno <= l <= node.end_lineno for l in removed):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names |= {n.id for t in targets for n in ast.walk(t) if isinstance(n, ast.Name)}
    return names


def changed_names(diff, before, exclude):
    """What a search for the stage's change would look for, leaving out the dependent's own file."""
    removed, left, names = set(), set(), set()
    for path, (lines, inserted, minus, plus) in _files(diff).items():
        if path == exclude or not path.endswith('.py'):
            continue
        removed |= _tokens(minus)
        left |= _tokens(plus)
        original = Path(before) / path
        if original.is_file():
            source = original.read_text(encoding='utf-8', errors='replace')
            # Removed outright means gone from every file the change touches, not just off one line.
            left |= _tokens([text for n, text in enumerate(source.splitlines(), 1) if n not in lines])
            names |= _definitions(source, lines, inserted)
    return names | (removed - left)


def named(names, path):
    text = Path(path).read_text(encoding='utf-8', errors='replace')
    return sorted(name for name in names if re.search(rf'(?<!\w){re.escape(name)}(?!\w)', text))


def suite_passes(tree, case, *, seconds=300):
    environment = {**os.environ, 'PYTHONPATH': str(Path(tree) / case['pythonpath']), 'PYTHONDONTWRITEBYTECODE': '1'}
    try:
        done = run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', case['test_dir']],
                   cwd=Path(tree), timeout=seconds, shell=False, env=environment)
    except subprocess.TimeoutExpired:
        return False
    return done.returncode == 0
