"""Partition candidates by specific witnesses, retaining broader fallbacks."""
from collections import defaultdict, deque
from dataclasses import asdict
from pathlib import PurePosixPath


def _python_test(path):
    name = PurePosixPath(path).name
    return name.startswith('test_') and name.endswith('.py') or name.endswith('_test.py')


def partition(graph, seeds, tests, *, max_depth, max_results):
    candidates = {}
    for node in tests:
        candidates.setdefault(node['path'], node)
    module_calls = {tuple(row) for row in graph.coverage.get('python_module_calls', [])}
    specific = {'calls', 'dynamic_import', 'fixture', 'fixture_definition', 'observed_call', 'observed_test', 'tests'}
    reverse = defaultdict(list)
    for edge in graph.edges:
        if edge.kind not in specific and not (edge.origin == 'declared' and edge.kind in ('uses', 'depends_on')):
            continue
        source = graph.nodes[edge.source]
        if edge.origin == 'static' and source.kind == 'file' and edge.path.endswith('.py'):
            if edge.kind in ('calls', 'dynamic_import') and (edge.path, edge.line, edge.target, edge.kind) not in module_calls:
                continue  # File aggregates cannot stand in for a called test/function.
        reverse[edge.target].append(edge)
    for rows in reverse.values():
        rows.sort(key=lambda e: (e.source, e.kind, e.path, e.line))
    queue = deque((identity, []) for identity in sorted(seeds))
    seen = set(seeds)
    focused = {}
    issues = []
    traversed = 0
    while queue:
        identity, suffix = queue.popleft()
        for edge in reverse[identity]:
            if edge.source in seen:
                continue
            if len(suffix) >= max_depth:
                issues.append('focused query depth limit reached')
                continue
            if traversed >= 50000:
                issues.append('focused query traversal limit 50000 reached')
                queue.clear()
                break
            traversed += 1
            seen.add(edge.source)
            witness = [edge, *suffix]
            node = graph.nodes[edge.source]
            queue.append((edge.source, witness))
            if node.path not in candidates or node.kind in ('fixture', 'fixture_binding'):
                continue
            if node.path.endswith('.py') and node.kind != 'test':
                if node.kind != 'file' or not _python_test(node.path):
                    continue
            if node.path in focused:
                continue
            if len(focused) >= max_results:
                issues.append('focused query result limit reached')
                continue
            origins = {e.origin for e in witness}
            category = 'declared' if 'declared' in origins else 'observed' if 'observed' in origins else (
                'direct' if len(witness) == 1 else 'transitive')
            focused[node.path] = {**asdict(node), 'distance': len(witness), 'category': category,
                                  'explanation': [asdict(e) for e in witness]}
    fallback, support = [], []
    for path, node in sorted(candidates.items()):
        if path in focused:
            continue
        if path.endswith('.py') and not _python_test(path) and node['kind'] != 'test':
            support.append(node)
        else:
            fallback.append(node)
    return {'focused': sorted(focused.values(), key=lambda n: (n['distance'], n['path'])),
            'fallback': fallback, 'support': support, 'safe_to_exclude_fallback': False,
            'policy': 'Focused witnesses rank possible checks; retain fallback/support and full verification. '
                      'Static calls and fixture requests are not execution or assertion coverage.'}, sorted(set(issues))
