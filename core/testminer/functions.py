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
    start: int = 0
    """The first decorator or the `def` line: where a change to the signature shows."""
    values: tuple[str, ...] = ('None',)
    """The extreme return values to try, as source, `None` first."""


VALUES = {
    'bool': ('True', 'False'), 'int': ('0', '1'), 'float': ('0.0', '1.0'), 'str': ("''", "'A'"),
    'bytes': ("b''", "b'A'"), 'list': ('[]', '[None]'), 'dict': ('{}', '{None: None}'),
    'set': ('set()', '{None}'), 'tuple': ('()', '(None,)'),
}
DISPLAYS = {ast.List: 'list', ast.Dict: 'dict', ast.Set: 'set', ast.Tuple: 'tuple', ast.JoinedStr: 'str',
            ast.Compare: 'bool'}


def _annotated(node: ast.expr | None) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        try:
            node = ast.parse(node.value, mode='eval').body
        except SyntaxError:
            return ''
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        sides = [side for side in (node.left, node.right) if not (isinstance(side, ast.Constant) and side.value is None)]
        return _annotated(sides[0]) if len(sides) == 1 else ''
    if isinstance(node, ast.Subscript):
        if _annotated(node.value) == 'optional':
            return _annotated(node.slice)
        node = node.value
    name = node.attr if isinstance(node, ast.Attribute) else node.id if isinstance(node, ast.Name) else ''
    return name.lower()


def _returns(node: ast.AST):
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        if isinstance(child, ast.Return):
            yield child.value
        yield from _returns(child)


def _kind(value: ast.expr | None) -> str:
    if isinstance(value, ast.UnaryOp) and isinstance(value.op, ast.Not):
        return 'bool'
    if isinstance(value, ast.Constant):
        return type(value.value).__name__
    return DISPLAYS.get(type(value), '')


def _values(node) -> tuple[str, ...]:
    if node.returns is not None:
        kind = _annotated(node.returns)
    else:
        kinds = {_kind(value) for value in _returns(node)}
        kind = kinds.pop() if len(kinds) == 1 else ''
    return ('None', *VALUES.get(kind, ()))


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
                    replaceable[0].lineno if replaceable else node.end_lineno, refused,
                    min([node.lineno, *(d.lineno for d in node.decorator_list)]), _values(node))


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
