"""Atomic validation of project assertions and unsigned, content-bound facts."""
import json
import re
import time

from ..redact import scrub
from .model import Edge, Node

NODE_KINDS = frozenset({'component', 'route', 'database', 'config', 'infrastructure', 'test'})
DECLARED_KINDS = frozenset({'depends_on', 'uses', 'tests'})
OBSERVED_KINDS = frozenset({'observed_call', 'observed_test'})
ID = re.compile(r'^[a-z][a-z0-9_-]*:[^\s]{1,180}$')


def text(value, field, limit=200):
    if (not isinstance(value, str) or not value.strip() or len(value) > limit
            or any(ord(c) < 32 for c in value)):
        raise ValueError('invalid ' + field)
    return scrub(value)


def rows(value, field):
    out = value.get(field, [])
    if not isinstance(out, list) or any(not isinstance(v, dict) for v in out):
        raise ValueError('invalid ' + field)
    if len(out) > 10000:
        raise ValueError('row limit 10000 exceeded')
    return out


def document(data):
    try:
        value = json.loads(data)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError('invalid JSON') from exc
    if not isinstance(value, dict) or type(value.get('schema')) is not int or value['schema'] != 1:
        raise ValueError('unsupported schema')
    return value


def edges(value, nodes, kinds, origin, path, identity, deadline):
    out = []
    for row in rows(value, 'edges'):
        if time.monotonic() >= deadline:
            raise ValueError('impact deadline reached validating edges')
        source, target, kind = row.get('source'), row.get('target'), row.get('kind')
        if not isinstance(source, str) or not isinstance(target, str) or source not in nodes or target not in nodes:
            raise ValueError('edge endpoint missing from selected graph')
        if not isinstance(kind, str) or kind not in kinds:
            raise ValueError('unsupported edge kind')
        out.append(Edge(source, target, kind, origin, path, 0, identity))
    return out


def declarations(graph, sources, deadline):
    path = 'impactgraph.json'
    if path not in sources:
        return
    try:
        value = document(sources[path])
        nodes = dict(graph.nodes)
        added = []
        for row in rows(value, 'nodes'):
            if time.monotonic() >= deadline:
                raise ValueError('impact deadline reached validating nodes')
            identity = row.get('id')
            kind = row.get('kind')
            if (not isinstance(identity, str) or not ID.fullmatch(identity)
                    or identity.startswith(('file:', 'symbol:')) or identity in nodes):
                raise ValueError('duplicate, reserved or invalid node ID')
            if not isinstance(kind, str) or kind not in NODE_KINDS:
                raise ValueError('unsupported node kind')
            anchor = row.get('path', '')
            if not isinstance(anchor, str) or (anchor and anchor not in sources):
                raise ValueError('node anchor is not a selected readable input')
            node = Node(identity, kind, text(row.get('label'), 'label'), anchor)
            added.append(node)
            nodes[identity] = node
        relations = edges(value, nodes, DECLARED_KINDS, 'declared', path, '', deadline)
    except ValueError as exc:
        graph.issues.append(f'declaration rejected: {exc}')
        return
    graph.nodes.update({n.id: n for n in added})
    for edge in relations:
        graph.add(edge)


def observations(graph, data, path, deadline):
    try:
        value = document(data)
        producer = text(value.get('producer'), 'producer')
        run = text(value.get('run'), 'run')
        if value.get('complete') is not True:
            raise ValueError('observation execution incomplete')
        fingerprint = value.get('source_fingerprint')
        if not isinstance(fingerprint, str) or fingerprint != graph.fingerprint:
            raise ValueError('observation source fingerprint is stale or invalid')
        if graph.issues:
            raise ValueError('current source/declaration coverage is incomplete')
        relations = edges(value, graph.nodes, OBSERVED_KINDS, 'observed', path,
                          producer + '/' + run, deadline)
    except ValueError as exc:
        graph.quarantined.append({'artifact': path, 'reason': str(exc)})
        graph.issues.append(f'observation quarantined: {exc}')
        return
    for edge in relations:
        graph.add(edge)
