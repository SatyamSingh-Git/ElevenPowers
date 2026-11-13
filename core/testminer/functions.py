"""Top-level functions and methods, with the body span a mutant replaces."""
from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class Function:
    name: str
    first: int
    last: int
    body: int
    refused: str


def _yields(node: ast.AST) -> bool:
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        if isinstance(child, (ast.Yield, ast.YieldFrom)) or _yields(child):
            return True
    return False


def _stub(statement: ast.stmt) -> bool:
    return isinstance(statement, ast.Pass) or (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant)
                                               and statement.value.value is Ellipsis)


def _function(node, name: str, lines: list[bytes]) -> Function:
    statements = node.body
    docstring = (isinstance(statements[0], ast.Expr) and isinstance(statements[0].value, ast.Constant)
                 and isinstance(statements[0].value.value, str))
    replaceable = statements[1:] if docstring else statements
    if isinstance(node, ast.AsyncFunctionDef):
        refused = 'async function'
    elif node.name == '__init__':
        refused = '__init__'
    elif _yields(node):
        refused = 'generator'
    elif not replaceable:
        refused = 'no statement besides a docstring'
    elif all(_stub(s) for s in replaceable):
        refused = 'body is only pass or ...'
    # col_offset counts UTF-8 bytes. A body that shares its line with the
    # signature cannot be replaced line by line.
    elif lines[statements[0].lineno - 1][:statements[0].col_offset].strip():
        refused = 'one-line function'
    else:
        refused = ''
    return Function(name, statements[0].lineno, node.end_lineno,
                    replaceable[0].lineno if replaceable else node.end_lineno, refused)


def functions(source: str) -> list[Function]:
    found = []
    lines = source.encode('utf-8').splitlines()
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.append(_function(node, node.name, lines))
        elif isinstance(node, ast.ClassDef):
            found += [_function(item, f'{node.name}.{item.name}', lines) for item in node.body
                      if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return sorted(found, key=lambda f: f.first)
