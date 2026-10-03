"""Optional Cosmic Ray producer, launched in a bounded child interpreter.

Operator enumeration follows Cosmic Ray's MIT-licensed commands/init.py.
No imports from this module are needed by the standard-library runtime.
"""
import hashlib
from collections import deque
from importlib.metadata import version
import json
from pathlib import Path
import sys


def main():
    from cosmic_ray.ast import ast_nodes, get_ast
    from cosmic_ray.plugins import get_operator, operator_names
    from cosmic_ray.mutating import mutate_code
    from cosmic_ray.util import read_python_source
    engine_version = version('cosmic-ray')
    if engine_version != '8.7.0':
        raise ValueError('supported Cosmic Ray version is 8.7.0')
    request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    if request.get('regions') is not None:
        print(json.dumps(targeted(request, engine_version)))
        return
    items = []
    more = False
    for path in request['paths']:
        if Path(path).stat().st_size > 1024 * 1024:
            raise ValueError('mutation source exceeds producer size limit')
        source = read_python_source(Path(path))
        for name in sorted(operator_names()):
            cls = get_operator(name)
            if cls.arguments():
                continue  # Operators requiring project-specific arguments are not guessed.
            operator = cls()
            positions = (pos for node in ast_nodes(get_ast(source))
                         for pos in operator.mutation_positions(node))
            for occurrence, (start, end) in enumerate(positions):
                if len(items) >= request['maximum']:
                    more = True
                    break
                content = mutate_code(source, operator, occurrence)
                if content is None or content == source:
                    continue
                identity = hashlib.sha256(f'{path}|{name}|{occurrence}'.encode()).hexdigest()[:24]
                items.append({'id': identity, 'path': path, 'line': start[0],
                              'operator': name, 'content': content})
            if more:
                break
        if more:
            break
    print(json.dumps({'version': engine_version, 'candidates': items, 'more': more}))


def targeted(request, engine_version):
    from cosmic_ray.ast import ast_nodes, get_ast
    from cosmic_ray.plugins import get_operator, operator_names
    from cosmic_ray.mutating import mutate_code
    from cosmic_ray.util import read_python_source
    from regions import validate, python_targets, location
    validate(request['regions'], request['paths'])
    sources, groups = {}, {}
    eligible = 0
    for path in request['paths']:
        if Path(path).stat().st_size > 1024 * 1024:
            raise ValueError('mutation source exceeds producer size limit')
        source = read_python_source(Path(path))
        changed = request['regions'][path]
        if any(end > len(source.splitlines()) for _, end in changed):
            raise ValueError('changed ranges exceed copied source')
        if not changed:
            continue
        sources[path] = source
        targets = python_targets(source, changed)
        nodes = tuple(ast_nodes(get_ast(source)))
        for name in sorted(operator_names()):
            cls = get_operator(name)
            if cls.arguments():
                continue
            operator = cls()
            positions = (pos for node in nodes for pos in operator.mutation_positions(node))
            for occurrence, (start, end) in enumerate(positions):
                last = max(start[0], end[0] - (end[1] == 0))
                match = location(start[0], last, changed, targets)
                if match is None:
                    continue
                relevance, context, target = match
                key = path, target
                groups.setdefault(key, []).append((name, occurrence, start[0], last, relevance, context))
                eligible += 1
                if eligible > 100000:
                    raise ValueError('eligible mutation enumeration limit exceeded')
    # Give each file a turn, then rotate its changed functions. A file with
    # many changed functions must not exhaust the sample before the next file.
    files = {}
    for key in sorted(groups):
        groups[key] = deque(sorted(groups[key], key=lambda item: (item[4] != 'changed_lines', item[0], item[1])))
        files.setdefault(key[0], deque()).append(key)
    turns, items = deque(files), []
    while turns and len(items) < request['maximum']:
        path = turns.popleft()
        key = files[path].popleft()
        name, occurrence, line, end_line, relevance, context = groups[key].popleft()
        content = mutate_code(sources[path], get_operator(name)(), occurrence)
        if content is not None and content != sources[path]:
            identity = hashlib.sha256(f'{path}|{name}|{occurrence}'.encode()).hexdigest()[:24]
            items.append({'id':identity, 'path':path, 'line':line, 'end_line':end_line,
                          'operator':name, 'content':content, 'relevance':relevance, 'context':context})
        if groups[key]:
            files[path].append(key)
        if files[path]:
            turns.append(path)
    return {'version':engine_version, 'candidates':items, 'more':bool(turns)}


if __name__ == '__main__':
    main()
