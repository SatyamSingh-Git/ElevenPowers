"""Optional Cosmic Ray producer, launched in a bounded child interpreter.

Operator enumeration follows Cosmic Ray's MIT-licensed commands/init.py.
No imports from this module are needed by the standard-library runtime.
"""
import hashlib
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


if __name__ == '__main__':
    main()
