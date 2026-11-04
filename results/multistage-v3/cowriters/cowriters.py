"""Same state: rank files by the rare fields and formats they share with what the edit writes.

A field is one name however it is spelled (`row.qty`, `row['qty']`, `{'qty': ...}`,
`Line(qty=...)`), so a producer that writes it meets a consumer that reads it.
Same interface as the co-readers scorer. See README.md for the plan, written
before this file.
"""
import ast
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'coreaders'))
sys.path.insert(0, str(HERE.parent / 'convention-spike'))
from coreaders import parsed  # noqa: E402
from rank import TEST_NAME, changed, sources  # noqa: E402


def _text(node):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _shape(node, found):
    """Format strings, and strings listed in a sequence (headers, orders)."""
    for item in ast.walk(node):
        if isinstance(item, (ast.List, ast.Tuple)):
            found.update('s:' + t for t in map(_text, item.elts) if t)
        value = _text(item)
        if value and ('%' in value or ('{' in value and '}' in value)):
            found.add('fmt:' + value)
        if isinstance(item, ast.JoinedStr):
            found.update('fmt:' + spec for spec in
                         (_text(v.format_spec.values[0]) for v in item.values
                          if isinstance(v, ast.FormattedValue) and v.format_spec and v.format_spec.values) if spec)


def written(node):
    found = set()
    for item in ast.walk(node):
        if isinstance(item, ast.Attribute) and isinstance(item.ctx, ast.Store):
            found.add('f:' + item.attr)
        elif isinstance(item, ast.Subscript) and isinstance(item.ctx, ast.Store) and _text(item.slice):
            found.add('f:' + _text(item.slice))
        elif isinstance(item, ast.Dict):
            found.update('f:' + t for t in map(_text, item.keys) if t)
        elif isinstance(item, ast.keyword) and item.arg:
            found.add('f:' + item.arg)
    _shape(node, found)
    return found


def touched(source, lines):
    tree = parsed(source)
    if tree is None or not lines:
        return set()
    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and any(n.lineno <= line <= n.end_lineno for line in lines)]
    chosen = [n for n in functions if not any(o is not n and n.lineno <= o.lineno and o.end_lineno <= n.end_lineno
                                              and any(o.lineno <= line <= o.end_lineno for line in lines)
                                              for o in functions)]
    if not chosen:
        chosen = [n for n in tree.body if any(n.lineno <= line <= n.end_lineno for line in lines)]
    found = set()
    for node in chosen:
        found |= written(node)
    return found


def state(tree):
    """Everything a file writes or reads of a field, plus its formats and listed strings."""
    found = written(tree)
    for item in ast.walk(tree):
        if isinstance(item, ast.Attribute):
            found.add('f:' + item.attr)
        elif isinstance(item, ast.Subscript) and _text(item.slice):
            found.add('f:' + _text(item.slice))
        elif (isinstance(item, ast.Call) and isinstance(item.func, ast.Attribute) and item.func.attr == 'get'
              and item.args and _text(item.args[0])):
            found.add('f:' + _text(item.args[0]))
    return found


def scored(before_tree, after_tree, edited):
    before, after = sources(before_tree), sources(after_tree)
    query = set()
    for path in edited:
        if path not in before or TEST_NAME.search(path):
            continue
        old, new = changed(before[path], after.get(path, ''))
        query |= touched(before[path], old) | touched(after.get(path, ''), new)
    documents = {}
    for path, text in before.items():
        tree = parsed(text)
        documents[path] = state(tree) if tree is not None else set()
    counts = {}
    for words in documents.values():
        for word in words:
            counts[word] = counts.get(word, 0) + 1
    idf = {word: math.log(len(documents) / count) for word, count in counts.items()}
    scores = sorted(((sum(idf.get(w, 0) for w in query & words), path) for path, words in documents.items()
                     if path not in edited), reverse=True)
    return scores, sum(idf.get(w, 0) for w in query), query, documents, idf
