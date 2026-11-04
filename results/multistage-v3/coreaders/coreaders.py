"""Co-readers: rank files by the rare inputs they read in common with the edited functions.

Same interface as the token spike's `scored`, so its three evaluations can run
unchanged with only the query and documents swapped. See README.md for the
plan, which was written before this file.
"""
import ast
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'convention-spike'))
from rank import TEST_NAME, changed, sources  # noqa: E402


def inputs_of(node):
    """Module constants, attribute reads and string keys read anywhere under `node`."""
    found = set()
    for item in ast.walk(node):
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load) and len(item.id) > 1 and item.id.isupper():
            found.add(item.id)
        elif isinstance(item, ast.Attribute) and isinstance(item.ctx, ast.Load):
            found.add('.' + item.attr)
        elif (isinstance(item, ast.Subscript) and isinstance(item.slice, ast.Constant)
              and isinstance(item.slice.value, str)):
            found.add(repr(item.slice.value))
        elif (isinstance(item, ast.Call) and isinstance(item.func, ast.Attribute) and item.func.attr.startswith('get')
              and item.args and isinstance(item.args[0], ast.Constant) and isinstance(item.args[0].value, str)):
            found.add(repr(item.args[0].value))
    return found


def parsed(source):
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def touched_inputs(source, lines):
    """Inputs of every function holding a changed line; of the changed top-level statements otherwise."""
    tree = parsed(source)
    if tree is None or not lines:
        return set()
    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and any(n.lineno <= line <= n.end_lineno for line in lines)]
    # The innermost function holding a line, so a method's change does not pull in its whole class.
    chosen = [n for n in functions if not any(o is not n and n.lineno <= o.lineno and o.end_lineno <= n.end_lineno
                                              and any(o.lineno <= line <= o.end_lineno for line in lines)
                                              for o in functions)]
    if not chosen:
        chosen = [n for n in tree.body if any(n.lineno <= line <= n.end_lineno for line in lines)]
    found = set()
    for node in chosen:
        found |= inputs_of(node)
    return found


def scored(before_tree, after_tree, edited):
    before, after = sources(before_tree), sources(after_tree)
    query = set()
    for path in edited:
        if path not in before or TEST_NAME.search(path):
            continue
        old, new = changed(before[path], after.get(path, ''))
        query |= touched_inputs(before[path], old) | touched_inputs(after.get(path, ''), new)
    documents = {}
    for path, text in before.items():
        tree = parsed(text)
        documents[path] = inputs_of(tree) if tree is not None else set()
    counts = {}
    for words in documents.values():
        for word in words:
            counts[word] = counts.get(word, 0) + 1
    idf = {word: math.log(len(documents) / count) for word, count in counts.items()}
    scores = sorted(((sum(idf.get(w, 0) for w in query & words), path) for path, words in documents.items()
                     if path not in edited), reverse=True)
    return scores, sum(idf.get(w, 0) for w in query), query, documents, idf
