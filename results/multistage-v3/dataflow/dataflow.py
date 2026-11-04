"""Data flow: rank files by how much they use what the change touched.

A file scores for every touched name it calls or reads (rarity-weighted), and at
half weight for every function that itself uses a touched name. Calls are
resolved by name only. Same interface as the earlier scorers; see README.md for
the plan, written before this file.
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


def touched_names(source, lines):
    """Names of the innermost functions holding a changed line; names a changed top-level statement binds."""
    tree = parsed(source)
    if tree is None or not lines:
        return set()
    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and any(n.lineno <= line <= n.end_lineno for line in lines)]
    inner = {n.name for n in functions if not any(
        o is not n and n.lineno <= o.lineno and o.end_lineno <= n.end_lineno
        and any(o.lineno <= line <= o.end_lineno for line in lines) for o in functions)}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and any(node.lineno <= line <= node.end_lineno for line in lines):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            inner |= {t.id for t in targets if isinstance(t, ast.Name)}
    return inner


def used(node):
    """Names a node calls or reads: plain names and attribute names."""
    found = set()
    for item in ast.walk(node):
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load):
            found.add(item.id)
        elif isinstance(item, ast.Attribute) and isinstance(item.ctx, ast.Load):
            found.add(item.attr)
    return found


def scored(before_tree, after_tree, edited):
    before, after = sources(before_tree), sources(after_tree)
    names = set()
    for path in edited:
        if path not in before or TEST_NAME.search(path):
            continue
        old, new = changed(before[path], after.get(path, ''))
        names |= touched_names(before[path], old) | touched_names(after.get(path, ''), new)
    functions, documents = {}, {}
    for path, text in after.items():
        tree = parsed(text)
        if tree is None:
            documents[path] = set()
            continue
        documents[path] = used(tree)
        functions[path] = [(n.name, used(n)) for n in ast.walk(tree)
                           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    counts = {}
    for words in documents.values():
        for word in words:
            counts[word] = counts.get(word, 0) + 1
    idf = {word: math.log(len(documents) / count) for word, count in counts.items()}
    # One hop up: functions anywhere that use a touched name, by their own names.
    callers = {name for rows in functions.values() for name, uses in rows if uses & names} - names
    scores = sorted(((sum(idf.get(w, 0) for w in names & words)
                      + .5 * sum(idf.get(w, 0) for w in callers & words), path)
                     for path, words in documents.items() if path not in edited and path in before),
                    reverse=True)
    total = sum(idf.get(w, 0) for w in names) + .5 * sum(idf.get(w, 0) for w in callers)
    return scores, total, names, documents, idf
