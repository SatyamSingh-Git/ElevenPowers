"""Resolve JS/TS specifiers only against safe, freshly selected project inputs."""
import json
import posixpath
import time
from pathlib import PurePosixPath

from .. import polyglot
from .model import Edge

EXTENSIONS = ('.ts', '.tsx', '.mts', '.cts', '.js', '.jsx', '.mjs', '.cjs')
CODE_SUFFIXES = frozenset(('.py', *EXTENSIONS, '.go', '.rs', '.rb', '.java', '.kt',
                         '.swift', '.c', '.h', '.cc', '.cpp', '.hpp', '.cs', '.php',
                         '.scala', '.ex', '.exs'))


def candidates(target, sources):
    target = posixpath.normpath(target)
    if target.startswith('../') or target == '..' or target.startswith('/'):
        return set()
    if target in sources:
        return {target}
    stem, ext = posixpath.splitext(target)
    if ext in ('.js', '.jsx', '.mjs', '.cjs'):
        substitutes = {'.js': ('.ts', '.tsx'), '.jsx': ('.tsx',),
                       '.mjs': ('.mts',), '.cjs': ('.cts',)}[ext]
        return {stem + e for e in substitutes if stem + e in sources}
    if ext:
        return set()
    return {p for e in EXTENSIONS for p in (target + e, target + '/index' + e) if p in sources}


def packages(sources, graph):
    found, external = {}, set()
    for path, data in sources.items():
        if PurePosixPath(path).name != 'package.json':
            continue
        try:
            value = json.loads(data)
            if not isinstance(value, dict):
                raise ValueError()
        except (ValueError, UnicodeError, RecursionError):
            graph.issues.append('package.json parse failed: ' + path)
            continue
        for section in ('dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies'):
            deps = value.get(section, {})
            if isinstance(deps, dict):
                external.update(deps)
        name = value.get('name')
        if isinstance(name, str) and name:
            found.setdefault(name, []).append((posixpath.dirname(path), value))
    return found, external


def resolve(spec, importer, sources, workspaces, external):
    if spec.startswith('.'):
        hits = candidates(posixpath.join(posixpath.dirname(importer), spec), sources)
    else:
        names = [n for n in workspaces if spec == n or spec.startswith(n + '/')]
        if not names:
            if spec.startswith('node:') or any(spec == n or spec.startswith(n + '/') for n in external):
                return '', 'external'
            return '', 'unresolved'
        name = max(names, key=len)
        entries = workspaces[name]
        if len(entries) != 1:
            return '', 'ambiguous'
        directory, value = entries[0]
        if 'exports' in value:
            return '', 'unresolved export map'
        suffix = spec[len(name):].lstrip('/')
        if suffix:
            hits = candidates(posixpath.join(directory, suffix), sources)
        else:
            declared = [value.get(k) for k in ('main', 'module', 'types') if isinstance(value.get(k), str)]
            entries = declared or ['src/index', 'index', 'src/main']
            hits = set().union(*(candidates(posixpath.join(directory, p), sources) for p in entries))
    if len(hits) == 1:
        return next(iter(hits)), ''
    return '', 'ambiguous' if hits else 'unresolved'


def extract_typescript(graph, sources, deadline):
    workspaces, external = packages(sources, graph)
    parsed = 0
    for path, data in sources.items():
        extension = PurePosixPath(path).suffix
        if extension not in EXTENSIONS:
            if extension in CODE_SUFFIXES and extension != '.py':
                graph.issues.append('unsupported source adapter: ' + path)
            continue
        if time.monotonic() >= deadline:
            graph.issues.append('impact deadline reached parsing JS/TS source')
            break
        if not polyglot.available():
            graph.issues.append('optional JS/TS grammar unavailable: ' + path)
            continue
        tree, _ = polyglot._parse(path, data)
        if tree is None or tree.root_node.has_error:
            graph.issues.append('JS/TS parse failed: ' + path)
            continue
        parsed += 1
        # A local binding can replace CommonJS require. Conservatively suppress
        # its calls anywhere in this file instead of pretending full TS scoping.
        shadowed_require = False
        bindings = [tree.root_node]
        while bindings:
            if time.monotonic() >= deadline:
                graph.issues.append('impact deadline reached resolving JS/TS bindings')
                break
            binding = bindings.pop()
            if binding.type in ('variable_declarator', 'function_declaration', 'required_parameter',
                                'optional_parameter', 'assignment_expression', 'import_specifier'):
                name = binding.child_by_field_name('name') or binding.child_by_field_name('pattern') or binding.child_by_field_name('left')
                if name is not None and name.text == b'require':
                    shadowed_require = True
            if binding.type == 'formal_parameters' and any(n.text == b'require' for n in binding.named_children):
                shadowed_require = True
            bindings.extend(binding.children)
        stack = [tree.root_node]
        while stack:
            if time.monotonic() >= deadline:
                graph.issues.append('impact deadline reached resolving JS/TS imports')
                break
            node = stack.pop()
            specifiers = []
            if node.type in ('import_statement', 'export_statement'):
                source = node.child_by_field_name('source')
                if source is not None:
                    specifiers = [source]
            elif node.type == 'call_expression':
                function = node.child_by_field_name('function')
                if function is not None and function.text == b'require':
                    if shadowed_require:
                        graph.issues.append(f'shadowed CommonJS require at {path}:{node.start_point[0] + 1}')
                        continue
                    args = node.child_by_field_name('arguments')
                    if args is not None and args.named_children and args.named_children[0].type == 'string':
                        specifiers = [args.named_children[0]]
                elif function is not None and function.type == 'import':
                    graph.issues.append(f'unresolved dynamic import: {path}:{node.start_point[0] + 1}')
            for source in specifiers:
                fragments = [n for n in source.named_children if n.type == 'string_fragment']
                if len(fragments) != 1:
                    graph.issues.append(f'unresolved escaped import: {path}:{node.start_point[0] + 1}')
                    continue
                spec = fragments[0].text.decode('utf-8', 'replace')
                target, problem = resolve(spec, path, sources, workspaces, external)
                if target and target != path:
                    graph.add(Edge('file:' + path, 'file:' + target, 'imports', 'static',
                                   path, node.start_point[0] + 1))
                elif problem != 'external' and not target:
                    graph.issues.append(f'{problem} JS/TS import at {path}:{node.start_point[0] + 1}')
            stack.extend(node.children)
    graph.coverage['parsed_typescript'] = parsed
