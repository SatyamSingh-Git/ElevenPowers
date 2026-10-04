"""Bound source-only pytest requests to selected definitions and test contexts.

This models default collection names and explicit fixture syntax, not pytest's
plugin/collection execution. No pytest import or target-code execution occurs.
"""
import ast
from collections import defaultdict
from pathlib import PurePosixPath
import time

from .model import Edge, Node
from .source import Bindings, callee, external_bindings, import_base, module_index, resolve_python


def _test_file(path):
    name = PurePosixPath(path).name
    return name.startswith('test_') and name.endswith('.py') or name.endswith('_test.py')


def _literal(node):
    if not isinstance(node, ast.Constant):
        raise ValueError('dynamic value')
    return node.value


def _strings(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        values = [v.strip() for v in node.value.split(',')]
    elif isinstance(node, (ast.List, ast.Tuple)):
        values = [_literal(v) for v in node.elts]
    else:
        raise ValueError('dynamic names')
    if not values or any(not isinstance(v, str) or not v.isidentifier() for v in values):
        raise ValueError('invalid names')
    return set(values)


def _required(node, method=False):
    if node.args.posonlyargs:
        raise ValueError('positional-only fixture arguments unsupported')
    args = node.args.args
    count = len(args) - len(node.args.defaults)
    names = [a.arg for a in args[:count]]
    if method and args:
        names = [n for n in names if n != args[0].arg]
    return set(names) | {a.arg for a, default in zip(node.args.kwonlyargs, node.args.kw_defaults)
                         if default is None}


def extract_fixtures(graph, trees, deadline):
    registry = defaultdict(lambda: defaultdict(list))
    uncertain = set()
    records = {}
    names = module_index(trees)

    def check():
        if time.monotonic() >= deadline:
            raise TimeoutError()

    def issue(message, path, line=0):
        graph.issues.append(f'{message} at {path}:{line}')

    def qualified(expr, record):
        text = callee(expr.func if isinstance(expr, ast.Call) else expr)
        root = text.split('.')[0]
        tool, valid = record['tools'].get(root, ('', False))
        name = tool + text[len(root):] if tool else ''
        return name, valid and root not in record['blocked']

    def fixture(node, record):
        decorators = [(d, *qualified(d, record)) for d in node.decorator_list]
        matches = [(d, valid) for d, name, valid in decorators if name == 'pytest.fixture']
        if not matches:
            return None
        registered = node.name
        try:
            if len(matches) != 1 or len(decorators) != 1 or not matches[0][1]:
                raise ValueError('unproven decorator or wrapper')
            decorator = matches[0][0]
            options = {}
            if isinstance(decorator, ast.Call):
                if decorator.args:
                    raise ValueError('positional registration unsupported')
                for k in decorator.keywords:
                    if k.arg not in ('name', 'scope', 'autouse', 'params', 'ids') or k.arg in options:
                        raise ValueError('expanded/unknown registration options')
                    options[k.arg] = k.value
            if 'name' in options:
                registered = _literal(options['name'])
                if not isinstance(registered, str) or not registered.isidentifier():
                    raise ValueError('dynamic registration name')
            autouse = _literal(options['autouse']) if 'autouse' in options else False
            scope = _literal(options['scope']) if 'scope' in options else 'function'
            if type(autouse) is not bool or scope not in ('function', 'class', 'module', 'package', 'session'):
                raise ValueError('dynamic autouse or scope')
            identity = 'symbol:' + record['path'] + '#' + node.name
            if identity not in graph.nodes:
                raise ValueError('rebound or ambiguous definition')
            required = _required(node)
            graph.nodes[identity] = Node(identity, 'fixture', registered, record['path'], node.lineno)
            return dict(name=registered, id=identity, path=record['path'], line=node.lineno,
                        required=required, autouse=autouse, valid=True)
        except ValueError as exc:
            issue('unsupported pytest fixture: ' + str(exc), record['path'], node.lineno)
            if not isinstance(registered, str) or not registered.isidentifier() or any(
                    isinstance(d, ast.Call) and any(k.arg == 'name' and not isinstance(k.value, ast.Constant)
                                                  for k in d.keywords) for d, _ in matches):
                uncertain.add(record['path'])
            return dict(name=node.name if not isinstance(registered, str) else registered,
                        valid=False, path=record['path'], line=node.lineno)

    def scopes(path):
        parents = PurePosixPath(path).parents
        return [path, *[(p / 'conftest.py').as_posix() for p in parents]]

    def marks(expressions, record):
        requests, direct = set(), set()
        for expr in expressions:
            check()
            if isinstance(expr, (ast.List, ast.Tuple)):
                nested, params = marks(expr.elts, record)
                requests |= nested; direct |= params
                continue
            name, valid = qualified(expr, record)
            if name not in ('pytest.mark.usefixtures', 'pytest.mark.parametrize'):
                if valid and name.startswith('pytest.mark.'):
                    continue
                if isinstance(expr, ast.Name) and expr.id in ('staticmethod', 'classmethod') and expr.id not in record['blocked']:
                    continue
                raise ValueError('unresolved decorator or pytest mark')
            if not valid or not isinstance(expr, ast.Call):
                raise ValueError('unproven fixture mark')
            if name.endswith('usefixtures'):
                if expr.keywords or not expr.args:
                    raise ValueError('unsupported usefixtures arguments')
                values = [_literal(a) for a in expr.args]
                if any(not isinstance(v, str) or not v.isidentifier() for v in values):
                    raise ValueError('usefixtures needs exact literal names')
                requests |= set(values)
            else:
                if len(expr.args) > 2:
                    raise ValueError('positional parametrize options unsupported')
                options = {k.arg: k.value for k in expr.keywords}
                if None in options or len(options) != len(expr.keywords):
                    raise ValueError('expanded/duplicate parametrize options')
                if expr.args and 'argnames' in options or len(expr.args) > 1 and 'argvalues' in options:
                    raise ValueError('duplicate parametrize arguments')
                argnames = expr.args[0] if expr.args else options.get('argnames')
                if argnames is None:
                    raise ValueError('missing parametrize names')
                supplied = _strings(argnames)
                indirect = options.get('indirect')
                if indirect is None:
                    direct |= supplied
                elif isinstance(indirect, ast.Constant) and type(indirect.value) is bool:
                    if not indirect.value: direct |= supplied
                else:
                    names_indirect = _strings(indirect)
                    if not names_indirect <= supplied:
                        raise ValueError('invalid indirect names')
                    direct |= supplied - names_indirect
        return requests, direct

    try:
        for path, tree in trees.items():
            check()
            bound = Bindings(deadline)
            for node in tree.body:
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    bound.visit(node)
            record = dict(path=path, tree=tree, tools=external_bindings(tree, 'pytest', names, deadline),
                          blocked=bound.names, counts=bound.counts)
            records[path] = record
            for node in tree.body:
                check()
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    meta = fixture(node, record)
                    if meta:
                        registry[path][meta['name']].append(meta)

        # Explicit registrations outside supported top-level definitions cannot
        # fall through to an ancestor and pretend that no override exists.
        for path, record in records.items():
            fixture_names = {m['id'].split('#')[-1] for rows in registry[path].values()
                             for m in rows if m.get('id')}
            for node in ast.walk(record['tree']):
                check()
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node not in record['tree'].body:
                    if any(qualified(d, record)[0] == 'pytest.fixture' for d in node.decorator_list):
                        uncertain.add(path)
                        issue('unsupported nested/class pytest fixture registration', path, node.lineno)
                elif isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                    if (qualified(node.value, record)[0] == 'pytest.fixture'
                            or isinstance(node.value, ast.Name) and node.value.id in fixture_names):
                        uncertain.add(path)
                        issue('unsupported assigned pytest fixture registration', path, node.lineno)
            for node in record['tree'].body:
                if not isinstance(node, ast.ImportFrom):
                    continue
                target, _ = resolve_python(import_base(node, path), names)
                if not target:
                    continue
                definitions = [m for rows in registry[target].values() for m in rows if m.get('id')]
                if any(m['id'] == 'symbol:' + target + '#' + a.name for a in node.names for m in definitions):
                    uncertain.add(path)
                    issue('unsupported imported pytest fixture registration', path, node.lineno)

        def candidates(context, name):
            return [meta for scope in scopes(context) for meta in registry[scope].get(name, [])]

        def request(context, source, name, stack, request_path, line):
            check()
            path = context['path']
            if name in context['direct']:
                return  # Direct parameter values replace fixture definitions.
            if any(scope in uncertain for scope in scopes(path)):
                issue('unresolved pytest fixture registration context', path, line)
                return
            rows = candidates(path, name)
            current = stack[-1] if stack else None
            # An override may request its own name from the next outer scope.
            if current and current['name'] == name:
                position = next((i for i, m in enumerate(rows) if m is current), -1)
                rows = rows[position + 1:] if position >= 0 else []
            if not rows or not rows[0]['valid']:
                issue('unresolved pytest fixture: ' + name, path, line)
                return
            meta = rows[0]
            if sum(m['path'] == meta['path'] for m in rows) > 1:
                issue('ambiguous pytest fixture: ' + name, path, line)
                return
            if any(m is meta for m in stack):
                issue('cyclic pytest fixture: ' + name, path, line)
                return
            identity = 'fixture:' + context['id'] + '#' + meta['id']
            if identity not in graph.nodes and len(graph.nodes) >= 50000:
                if 'pytest fixture node limit 50000 reached' not in graph.issues:
                    graph.issues.append('pytest fixture node limit 50000 reached')
                return
            graph.nodes[identity] = Node(identity, 'fixture_binding', name, meta['path'], meta['line'])
            graph.add(Edge(identity, meta['id'], 'fixture_definition', 'static', meta['path'], meta['line']))
            graph.add(Edge(source, identity, 'fixture', 'static', request_path, line, 'pytest:' + name))
            # Dependencies are resolved in this requesting context, not globally.
            for dependency in sorted(meta['required']):
                request(context, identity, dependency, [*stack, meta], meta['path'], meta['line'])

        def test(node, record, inherited=(), method=False, prefix='', blocked_class=False):
            check()
            path = record['path']
            identity = 'symbol:' + path + '#' + prefix + node.name
            if blocked_class or any(qualified(d, record)[0] == 'pytest.fixture' for d in node.decorator_list):
                return
            if not prefix and identity not in graph.nodes:
                issue('rebound pytest test definition', path, node.lineno)
                return
            graph.nodes[identity] = Node(identity, 'test', prefix + node.name, path, node.lineno)
            graph.add(Edge('file:' + path, identity, 'defines', 'static', path, node.lineno))
            try:
                if record.get('marks_rebound'):
                    raise ValueError('rebound module pytest marks')
                required = _required(node, method)
                requested, direct = marks([*inherited, *node.decorator_list], record)
                requested |= required - direct
            except ValueError as exc:
                issue('unsupported pytest fixture request: ' + str(exc), path, node.lineno)
                return
            requested |= {name for scope in scopes(path) for name, rows in registry[scope].items()
                          if any(m.get('autouse') for m in rows)}
            context = dict(path=path, id=identity, direct=direct)
            for name in sorted(requested - direct):
                request(context, identity, name, [], path, node.lineno)

        for path, record in records.items():
            check()
            if not _test_file(path):
                continue
            inherited = []
            record['marks_rebound'] = record['counts'].get('pytestmark', 0) > 1
            if record['marks_rebound']:
                issue('rebound module pytest marks', path)
            for node in record['tree'].body:
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    if any(isinstance(t, ast.Name) and t.id == 'pytestmark' for t in targets) and node.value:
                        inherited.append(node.value)
            for node in record['tree'].body:
                check()
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test'):
                    test(node, record, inherited)
                elif isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                    if 'symbol:' + path + '#' + node.name not in graph.nodes or node.bases:
                        issue('unsupported or rebound pytest class', path, node.lineno)
                        continue
                    class_fixtures = [m for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                                      and any(qualified(d, record)[0] == 'pytest.fixture' for d in m.decorator_list)]
                    if class_fixtures:
                        issue('unsupported class pytest fixture registration', path, node.lineno)
                    bound = Bindings(deadline)
                    for child in node.body: bound.visit(child)
                    for method in node.body:
                        if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) and method.name.startswith('test'):
                            if bound.counts[method.name] != 1:
                                issue('rebound pytest class test definition', path, method.lineno)
                                continue
                            static = any(isinstance(d, ast.Name) and d.id == 'staticmethod' for d in method.decorator_list)
                            test(method, record, [*inherited, *node.decorator_list], not static,
                                 node.name + '.', bool(class_fixtures))
    except (TimeoutError, RecursionError):
        graph.issues.append('pytest fixture deadline or traversal limit reached')
    graph.coverage['pytest_fixtures'] = sum(m.get('valid', False) for by_name in registry.values()
                                          for rows in by_name.values() for m in rows)
    graph.coverage['pytest_collection'] = 'Static default file/function/class names; plugins and collection are not executed.'
