"""Portable typed relationships; direction is dependent -> dependency."""
from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class Node:
    id: str
    kind: str
    label: str
    path: str = ''
    line: int = 0


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    kind: str
    origin: str
    path: str = ''
    line: int = 0
    identity: str = ''


@dataclass
class Graph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    fingerprint: str = ''
    coverage: dict = field(default_factory=dict)
    associations: list[dict] = field(default_factory=list)
    quarantined: list[dict] = field(default_factory=list)
    _seen: set[Edge] = field(default_factory=set, repr=False)

    def add(self, edge: Edge):
        if edge in self._seen:
            return
        if len(self.edges) >= 50000:
            if 'graph edge limit 50000 reached' not in self.issues:
                self.issues.append('graph edge limit 50000 reached')
            return
        self._seen.add(edge)
        self.edges.append(edge)

    def to_dict(self):
        return {'schema': 1, 'source_fingerprint': self.fingerprint,
                'nodes': [asdict(self.nodes[k]) for k in sorted(self.nodes)],
                'edges': [asdict(e) for e in sorted(self.edges, key=lambda e:
                          (e.source, e.target, e.kind, e.origin, e.path, e.line, e.identity))],
                'coverage': {**self.coverage, 'complete': not self.issues,
                             'issues': sorted(set(self.issues))},
                'associations': self.associations, 'quarantined': self.quarantined,
                'limits': ['Selection completeness is not exhaustive semantic coverage.',
                           'Static calls describe unambiguous imported Python bindings, not runtime dispatch.',
                           'Declared relationships are project assertions; observed relationships are unsigned.',
                           'Test relationships suggest checks; they do not establish passing assertions.',
                           'Co-change is association, not causation or a breakage probability.',
                           'Fresh reads are a bounded filesystem snapshot, not an atomic transaction.']}
