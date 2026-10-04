"""Source extraction reuses Python AST and the existing optional grammar pack."""
import ast
import time
from collections import defaultdict

from .model import Edge, Node


def module_index(paths):
    names = defaultdict(set)
    for path in paths:
        if not path.endswith('.py'):
            continue
        parts = path[:-3].split('/')
        if parts[-1] == '__init__':
            parts.pop()
        for start in range(len(parts)):
            names['.'.join(parts[start:])].add(path)
    return names


def resolve_python(name, names):
    candidates = names.get(name, set())
    if len(candidates) == 1:
        return next(iter(candidates)), ''
    return '', 'ambiguous' if candidates else 'unresolved'


def import_base(node, path):
    if not node.level:
        return node.module or ''
    parts = path.split('/')[:-1]
    if node.level > len(parts):
        return ''
    prefix = '.'.join(parts[:len(parts) - node.level + 1])
    return '.'.join(p for p in (prefix, node.module) if p)


class Bindings(ast.NodeVisitor):
    """Conservatively collect bindings in one scope, without entering children."""
    def __init__(self):
        self.names = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.names.add(node.id)

    def visit_arg(self, node):
        self.names.add(node.arg)

    def visit_FunctionDef(self, node):
        self.names.add(node.name)

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef

    def visit_Import(self, node):
        self.names.update(a.asname or a.name.split('.')[0] for a in node.names)

    def visit_ImportFrom(self, node):
        self.names.update(a.asname or a.name for a in node.names)

    def visit_ExceptHandler(self, node):
        if node.name:
            self.names.add(node.name)
        self.generic_visit(node)


def scope_bindings(nodes):
    found = Bindings()
    for node in nodes:
        found.visit(node)
    return found.names


def python_edges(graph, path, tree, names):
    bindings = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        base = import_base(node, path) if isinstance(node, ast.ImportFrom) else ''
        for alias in node.names:
            name = alias.name if isinstance(node, ast.Import) else '.'.join(
                p for p in (base, alias.name) if p)
            target, problem = resolve_python(name, names)
            is_module = bool(target)
            if not target and isinstance(node, ast.ImportFrom) and base:
                target, problem = resolve_python(base, names)
            if target:
                if target != path:
                    graph.add(Edge('file:' + path, 'file:' + target, 'imports',
                                   'static', path, node.lineno))
                # Only unconditional module-level imports supply call bindings.
                if node in tree.body and alias.name != '*':
                    if isinstance(node, ast.Import):
                        key = alias.asname or alias.name
                        bindings[key] = ('module', target)
                    elif is_module:
                        bindings[alias.asname or alias.name] = ('module', target)
                    else:
                        bindings[alias.asname or alias.name] = ('symbol', target + '#' + alias.name)
            elif problem == 'ambiguous' or (isinstance(node, ast.ImportFrom) and node.level):
                graph.issues.append(f'{problem} Python import at {path}:{node.lineno}')
    # Assignment/redefinition anywhere in the module invalidates a call binding.
    blocked = scope_bindings([n for n in tree.body if not isinstance(n, (ast.Import, ast.ImportFrom))])

    def walk(node, shadows):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            args = scope_bindings([node.args])
            body = node.body if isinstance(node.body, list) else [node.body]
            local = scope_bindings(body)
            # Defaults and decorators execute in the enclosing scope.
            for part in [*node.args.defaults, *[v for v in node.args.kw_defaults if v],
                         *getattr(node, 'decorator_list', [])]:
                walk(part, shadows)
            for child in body:
                walk(child, shadows | args | local)
            return
        if isinstance(node, ast.ClassDef):
            # Class-bound names cannot be confidently treated as module aliases.
            for child in node.body:
                walk(child, shadows | scope_bindings(node.body))
            return
        if isinstance(node, ast.Call):
            text = ast.unparse(node.func)
            for key, (kind, target) in bindings.items():
                if text != key and not text.startswith(key + '.'):
                    continue
                if key.split('.')[0] in shadows:
                    graph.issues.append(f'shadowed Python call binding at {path}:{node.lineno}')
                    break
                suffix = text[len(key):].lstrip('.')
                identity = 'symbol:' + target if kind == 'symbol' and not suffix else (
                    'symbol:' + target + '#' + suffix if kind == 'module' and suffix else '')
                if identity in graph.nodes:
                    graph.add(Edge('file:' + path, identity, 'calls', 'static', path, node.lineno))
                else:
                    graph.coverage['unresolved_calls'] += 1
                break
        for child in ast.iter_child_nodes(node):
            walk(child, shadows)
    walk(tree, blocked)


def extract(graph, sources, deadline):
    trees = {}
    for path, data in sources.items():
        if time.monotonic() >= deadline:
            graph.issues.append('impact deadline reached parsing source')
            break
        if not path.endswith('.py'):
            continue
        try:
            tree = ast.parse(data, filename=path)
        except (SyntaxError, ValueError, RecursionError):
            graph.issues.append(f'Python parse failed: {path}')
            continue
        trees[path] = tree
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                identity = f'symbol:{path}#{node.name}'
                graph.nodes[identity] = Node(identity, 'symbol', node.name, path, node.lineno)
    names = module_index(sources)
    for path, tree in trees.items():
        if time.monotonic() >= deadline:
            graph.issues.append('impact deadline reached resolving source')
            break
        python_edges(graph, path, tree, names)
    graph.coverage['parsed_python'] = len(trees)
