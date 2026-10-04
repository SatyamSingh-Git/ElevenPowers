"""Explicit trusted TypeScript compiler; consumes a virtual selected snapshot.

Borrows Microsoft's compiler API (Apache-2.0), not a second TS resolver. Adds
bounded containment and graph endpoint validation; this is not type checking.
"""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from ..process import run
from .model import Edge, Node
from .typescript import EXTENSIONS


def validate(value, sources):
    if (not isinstance(value, dict) or type(value.get('schema')) is not int or value.get('schema') != 1
            or value.get('version') != '5.7.3'):
        raise ValueError('unsupported compiler result/version (qualified: 5.7.3)')
    nodes, edges, issues = value.get('nodes'), value.get('edges'), value.get('issues')
    if (not isinstance(nodes, list) or len(nodes) > 20000
            or not isinstance(edges, list) or len(edges) > 50000
            or not isinstance(issues, list) or len(issues) > 1000
            or any(not isinstance(i, str) or len(i) > 600 for i in issues)):
        raise ValueError('invalid or oversized compiler rows')
    known = {'file:' + p for p in sources}
    added = []
    for row in nodes:
        if not isinstance(row, dict):
            raise ValueError('invalid compiler node')
        path, identity, label, line = (row.get(k) for k in ('path', 'id', 'label', 'line'))
        if (not isinstance(path, str) or path not in sources or row.get('kind') != 'symbol'
                or not isinstance(identity, str) or not identity.startswith('symbol:' + path + '#')
                or len(identity) > 700 or identity in known
                or not isinstance(label, str) or not 1 <= len(label) <= 300
                or type(line) is not int or not 1 <= line <= 1000000):
            raise ValueError('invalid compiler symbol endpoint')
        known.add(identity)
        added.append(Node(identity, 'symbol', label, path, line))
    relations = []
    for row in edges:
        if not isinstance(row, dict):
            raise ValueError('invalid compiler edge')
        source, target, kind, path, line = (row.get(k) for k in ('source', 'target', 'kind', 'path', 'line'))
        if (not isinstance(source, str) or not isinstance(target, str)
                or source not in known or target not in known or kind not in ('imports', 'calls')
                or not isinstance(path, str) or path not in sources or source != 'file:' + path
                or type(line) is not int or not 1 <= line <= 1000000):
            raise ValueError('invalid compiler edge endpoint')
        relations.append(Edge(source, target, kind, 'static', path, line, 'typescript/5.7.3'))
    return added, relations, issues


def extract_compiler(graph, sources, engine, config, deadline):
    started = time.monotonic()
    graph.coverage['typescript_compiler'] = {'complete': False}
    try:
        engine = Path(engine).resolve(strict=True)
        if not engine.is_file():
            raise ValueError('compiler engine is not a file')
        node = shutil.which('node')
        if not node:
            raise ValueError('Node is unavailable for compiler')
        selected = {p: b.decode('utf-8-sig') for p, b in sources.items()
                    if p.endswith(EXTENSIONS) or p.endswith('.json')}
        if len(selected) > 5000:
            raise ValueError('compiler input file limit 5000 exceeded')
        payload = json.dumps({'schema': 1, 'sources': selected, 'config': config}, ensure_ascii=False)
        if len(payload.encode()) > 32 * 1024 * 1024:
            raise ValueError('compiler input byte limit 32 MiB exceeded')
        if time.monotonic() >= deadline:
            raise ValueError('impact deadline reached before compiler')
        with tempfile.TemporaryDirectory(prefix='ep-impact-compiler-') as private:
            entry = Path(private) / 'inputs.json'
            entry.write_text(payload, encoding='utf-8')
            done = run([node, str(Path(__file__).with_suffix('.cjs')), str(engine), str(entry)],
                       cwd=Path(private), shell=False, timeout=max(.001, deadline-time.monotonic()))
        if done.returncode:
            raise ValueError('compiler worker failed: ' + done.stderr[-600:])
        value = json.loads(done.stdout)
        nodes, edges, issues = validate(value, sources)
        if time.monotonic() >= deadline:
            raise ValueError('impact deadline reached validating compiler')
        graph.nodes.update({n.id: n for n in nodes})
        for edge in edges:
            graph.add(edge)
        graph.issues.extend(issues)
        graph.coverage['typescript_compiler'].update(version=value['version'], complete=not issues,
            files=value.get('files'), unresolved_calls=value.get('unresolved_calls'),
            config=value.get('config'), engine_trust='explicit executable compiler path')
    except (OSError, ValueError, UnicodeError, RecursionError, subprocess.SubprocessError) as exc:
        graph.issues.append('TypeScript compiler unavailable or incomplete: ' + str(exc))
    graph.coverage['typescript_compiler']['seconds'] = time.monotonic() - started
