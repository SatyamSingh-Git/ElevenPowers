"""Source extraction reuses Python AST and the existing optional grammar pack."""
import ast
import time
from collections import defaultdict, Counter
from importlib.util import resolve_name

from .model import Edge, Node


def module_index(paths):
    names = defaultdict(set)
    for path in paths:
        if not path.endswith('.py'):
            continue
        parts = path[:-3].split('/')
        if parts[-1] == '__init__':
            parts.pop()
        names['.'.join(parts)].add(path)
        if parts and parts[0] == 'src':
            names['.'.join(parts[1:])].add(path)
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
    def __init__(self, deadline=float('inf')):
        self.names = set()
        self.counts = Counter()
        self.deadline = deadline

    def add(self, name):
        if name:
            self.names.add(name)
            self.counts[name] += 1

    def visit(self, node):
        if time.monotonic() >= self.deadline:
            raise TimeoutError()
        return super().visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.add(node.id)

    def visit_arg(self, node):
        self.add(node.arg)

    def visit_FunctionDef(self, node):
        self.add(node.name)

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef

    def visit_Import(self, node):
        for alias in node.names:
            self.add(alias.asname or alias.name.split('.')[0])

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.add(alias.asname or alias.name)

    def visit_ExceptHandler(self, node):
        if node.name:
            self.add(node.name)
        self.generic_visit(node)

    def visit_MatchAs(self, node):
        self.add(node.name)
        self.generic_visit(node)

    visit_MatchStar = visit_MatchAs

    def visit_MatchMapping(self, node):
        self.add(node.rest)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.add(callee(node).split('.')[0])
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in ('setattr', 'delattr') and node.args:
            self.add(callee(node.args[0]).split('.')[0])
        self.generic_visit(node)


def scope_bindings(nodes, deadline=float('inf')):
    found = Bindings(deadline)
    for node in nodes:
        found.visit(node)
    return found.names


def callee(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = callee(node.value)
        return base + '.' + node.attr if base else ''
    return ''


def external_bindings(tree, module, names, deadline):
    """Recognize imported tool names, while retaining unsafe names as gaps."""
    tools = {}
    for node in tree.body:
        if time.monotonic() >= deadline:
            raise TimeoutError()
        rows = []
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == module or alias.name.startswith(module + '.'):
                    rows.append((alias.asname or module,
                                 alias.name if alias.asname else module))
                else:
                    rows.append((alias.asname or alias.name.split('.')[0], None))
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                rows.append((alias.asname or alias.name,
                             module + '.' + alias.name if node.module == module and not node.level else None))
        for key, qualified in rows:
            if key in tools and tools[key][0] != qualified:
                tools[key] = (tools[key][0] or qualified, False)
            elif qualified:
                tools[key] = (qualified, key not in tools or tools[key][1])
            else:
                tools.setdefault(key, (None, False))
    local = bool(names.get(module))
    return {k: (q, valid and not local) for k, (q, valid) in tools.items() if q}


def literal_module(call):
    """Resolve only literal import_module arguments; never evaluate expressions."""
    if len(call.args) > 2 or any(isinstance(a, ast.Starred) for a in call.args):
        raise ValueError('unsupported arguments')
    values = dict(zip(('name', 'package'), call.args))
    for keyword in call.keywords:
        if keyword.arg not in ('name', 'package') or keyword.arg in values:
            raise ValueError('unknown, expanded or duplicate arguments')
        values[keyword.arg] = keyword.value
    name = values.get('name')
    package = values.get('package')
    if not isinstance(name, ast.Constant) or not isinstance(name.value, str) or len(name.value) > 500:
        raise ValueError('non-literal module name')
    if package is not None and (not isinstance(package, ast.Constant)
                               or package.value is not None and not isinstance(package.value, str)):
        raise ValueError('non-literal package anchor')
    anchor = package.value if package is not None else None
    result = resolve_name(name.value, anchor)
    if not result or not all(p.isidentifier() for p in result.split('.')):
        raise ValueError('unsupported module name')
    return result


def python_edges(graph, path, tree, names, exports, deadline):
    bindings = {}
    tools = external_bindings(tree, 'importlib', names, deadline)
    for node in ast.walk(tree):
        if time.monotonic() >= deadline:
            raise TimeoutError()
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        base = import_base(node, path) if isinstance(node, ast.ImportFrom) else ''
        if isinstance(node, ast.ImportFrom) and node.level and not base:
            graph.issues.append(f'unresolved beyond-root Python import at {path}:{node.lineno}')
            continue
        for alias in node.names:
            if time.monotonic() >= deadline:
                raise TimeoutError()
            name = alias.name if isinstance(node, ast.Import) else '.'.join(
                p for p in (base, alias.name) if p)
            target, problem = resolve_python(name, names)
            is_module = bool(target)
            if isinstance(node, ast.ImportFrom) and base:
                package, ambiguity = resolve_python(base, names)
                if package and alias.name in exports.get(package, set()):
                    # Existing package attributes win over same-name submodules.
                    target, problem, is_module = package, '', False
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
            elif (problem == 'ambiguous' or (isinstance(node, ast.ImportFrom) and node.level)
                  or any(n.endswith('.' + name.split('.')[0]) for n in names)):
                graph.issues.append(f'{problem} Python import at {path}:{node.lineno}')
    # Assignment/redefinition anywhere in the module invalidates a call binding.
    blocked = scope_bindings([n for n in tree.body if not isinstance(n, (ast.Import, ast.ImportFrom))], deadline)

    local_bindings = {name: 'symbol:' + path + '#' + name for name in exports.get(path, set())
                      if 'symbol:' + path + '#' + name in graph.nodes}

    def walk(node, shadows, owner='', local_shadows=frozenset()):
        if time.monotonic() >= deadline:
            raise TimeoutError()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            args = scope_bindings([node.args], deadline)
            body = node.body if isinstance(node.body, list) else [node.body]
            local = scope_bindings(body, deadline)
            # Defaults and decorators execute in the enclosing scope.
            for part in [*node.args.defaults, *[v for v in node.args.kw_defaults if v],
                         *getattr(node, 'decorator_list', [])]:
                walk(part, shadows, owner, local_shadows)
            identity = 'symbol:' + path + '#' + getattr(node, 'name', '')
            next_owner = identity if node in tree.body and identity in graph.nodes else ''
            for child in body:
                walk(child, shadows | args | local, next_owner, local_shadows | args | local)
            return
        if isinstance(node, ast.ClassDef):
            # Class-bound names cannot be confidently treated as module aliases.
            for child in node.body:
                bound = scope_bindings(node.body, deadline)
                walk(child, shadows | bound, local_shadows=local_shadows | bound)
            return
        if isinstance(node, ast.Call):
            text = callee(node.func)
            parts = text.split('.')
            if text in local_bindings and text not in local_shadows:
                for source in filter(None, ('file:' + path, owner)):
                    graph.add(Edge(source, local_bindings[text], 'calls', 'static', path, node.lineno))
            tool, valid = tools.get(parts[0], ('', False))
            if tool + text[len(parts[0]):] == 'importlib.import_module':
                try:
                    if not valid or parts[0] in shadows:
                        raise ValueError('shadowed, rebound or local tool binding')
                    name = literal_module(node)
                    target, problem = resolve_python(name, names)
                    if not target:
                        raise ValueError(problem)
                    for source in filter(None, ('file:' + path, owner)):
                        graph.add(Edge(source, 'file:' + target, 'dynamic_import',
                                       'static', path, node.lineno, 'importlib.import_module'))
                except (ValueError, ImportError) as exc:
                    graph.issues.append(f'{exc} dynamic import at {path}:{node.lineno}')
            for length in range(len(parts), 0, -1):
                key = '.'.join(parts[:length])
                if key not in bindings:
                    continue
                kind, target = bindings[key]
                if key.split('.')[0] in shadows:
                    graph.issues.append(f'shadowed Python call binding at {path}:{node.lineno}')
                    break
                suffix = text[len(key):].lstrip('.')
                identity = 'symbol:' + target if kind == 'symbol' and not suffix else (
                    'symbol:' + target + '#' + suffix if kind == 'module' and suffix else '')
                if identity in graph.nodes:
                    graph.add(Edge('file:' + path, identity, 'calls', 'static', path, node.lineno))
                    if owner:
                        graph.add(Edge(owner, identity, 'calls', 'static', path, node.lineno))
                        target_path = target.split('#', 1)[0]
                        if target_path != path:
                            graph.add(Edge(owner, 'file:' + target_path, 'uses',
                                           'static', path, node.lineno, 'python:qualified-call-module'))
                else:
                    graph.coverage['unresolved_calls'] += 1
                break
        for child in ast.iter_child_nodes(node):
            walk(child, shadows, owner, local_shadows)
    walk(tree, blocked)


def extract(graph, sources, deadline):
    trees, exports = {}, {}
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
        try:
            bound = Bindings(deadline)
            for node in tree.body:
                bound.visit(node)
        except (TimeoutError, RecursionError):
            graph.issues.append('impact deadline or AST traversal limit reached collecting exports')
            break
        trees[path] = tree
        exports[path] = bound.names
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if bound.counts[node.name] != 1:
                    graph.issues.append(f'ambiguous or rebound Python export: {path}:{node.lineno}')
                    continue
                identity = f'symbol:{path}#{node.name}'
                graph.nodes[identity] = Node(identity, 'symbol', node.name, path, node.lineno)
                graph.add(Edge('file:' + path, identity, 'defines', 'static', path, node.lineno))
    names = module_index(sources)
    for path, tree in trees.items():
        if time.monotonic() >= deadline:
            graph.issues.append('impact deadline reached resolving source')
            break
        try:
            python_edges(graph, path, tree, names, exports, deadline)
        except (TimeoutError, RecursionError):
            graph.issues.append('impact deadline or AST traversal limit reached resolving source')
            break
    graph.coverage['parsed_python'] = len(trees)
    return trees
