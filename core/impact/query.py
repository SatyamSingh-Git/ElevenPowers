"""Reverse dependency witnesses, without inferring probabilities or correctness."""
from collections import defaultdict, deque
from dataclasses import asdict

from ..redact import scrub
from ..surface import TEST_NAME


def analyze(graph, files, *, max_depth=6, max_results=100):
    if type(max_depth) is not int or not 1 <= max_depth <= 20:
        raise ValueError('max_depth must be between 1 and 20')
    if type(max_results) is not int or not 1 <= max_results <= 1000:
        raise ValueError('max_results must be between 1 and 1000')
    if not isinstance(files, (list, tuple)) or not files or any(not isinstance(p, str) or not p for p in files):
        raise ValueError('query needs at least one relative file path or node ID')
    issues = list(graph.issues)
    seeds = set()
    seed_paths = set()
    for value in files:
        if value in graph.nodes:
            seeds.add(value)
            if graph.nodes[value].path:
                seed_paths.add(graph.nodes[value].path)
        else:
            matches = {n.id for n in graph.nodes.values() if n.path == value}
            if not matches:
                issues.append('query input missing, excluded, deleted or unsupported: ' + value)
            seeds.update(matches)
            seed_paths.add(value)
    reverse = defaultdict(list)
    priority = {'calls': 0, 'observed_call': 1, 'observed_test': 1, 'tests': 2,
                'uses': 2, 'depends_on': 2, 'imports': 3}
    for edge in graph.edges:
        reverse[edge.target].append(edge)
    for relations in reverse.values():
        relations.sort(key=lambda e: (priority.get(e.kind, 4), e.source, e.path, e.line))
    # Imported-symbol witnesses can be more specific than a file import.
    queue = deque((key, []) for key in sorted(seeds, key=lambda k: (graph.nodes[k].kind != 'symbol', k)))
    seen = set(seeds)
    found = []
    while queue:
        node, suffix = queue.popleft()
        for edge in reverse[node]:
            if edge.source in seen:
                continue
            if len(suffix) >= max_depth:
                if 'query depth limit reached' not in issues:
                    issues.append('query depth limit reached')
                continue
            if len(found) >= max_results:
                if 'query result limit reached' not in issues:
                    issues.append('query result limit reached')
                queue.clear()
                break
            seen.add(edge.source)
            path = [edge, *suffix]
            candidate = graph.nodes[edge.source]
            queue.append((edge.source, path))
            if candidate.path in seed_paths or candidate.kind == 'fixture_binding':
                continue
            origins = {e.origin for e in path}
            category = 'declared' if 'declared' in origins else 'observed' if 'observed' in origins else (
                'direct' if len(path) == 1 else 'transitive')
            found.append({**asdict(candidate), 'distance': len(path), 'category': category,
                          'explanation': [asdict(e) for e in path]})
    found.sort(key=lambda n: (n['distance'], n['id']))
    tests = [n for n in found if n['kind'] == 'test' or TEST_NAME.search(n['path'])]
    affected = [n for n in found if n not in tests]
    associations = {}
    for item in graph.associations:
        for source, target in ((item['source'], item['target']), (item['target'], item['source'])):
            if source in seeds and target not in seen and target in graph.nodes:
                candidate = graph.nodes[target]
                associations.setdefault(target, {**asdict(candidate), 'origin': 'historical', 'commits': []})
                associations[target]['commits'].append(item['commit'])
    association_values = sorted(associations.values(), key=lambda n: n['id'])
    if len(association_values) > max_results:
        issues.append('association result limit reached')
        association_values = association_values[:max_results]
    snapshot = graph.to_dict()
    return {'schema': 1, 'source_fingerprint': graph.fingerprint, 'requested': list(files),
            'summary': f'{len(affected)} affected nodes; {len(tests)} candidate tests' if found else
                       'No current dependency path found within the selected scope.',
            'affected': affected, 'tests': tests, 'associations': association_values,
            'quarantined': graph.quarantined,
            'coverage': {**snapshot['coverage'], 'complete': not issues, 'issues': sorted(set(issues))},
            'limits': snapshot['limits']}


def markdown(report):
    def escape(value):
        value = scrub(str(value))
        return value.replace('`', '\\`').replace('*', '\\*').replace('<', '&lt;').replace('>', '&gt;')
    lines = ['# ImpactGraph', '', report['summary'], '',
             'Input fingerprint: `' + report['source_fingerprint'] + '`', '']
    if report.get('change'):
        lines += ['Requested change: ' + escape(report['change']), '']
    for title, key in (('Affected components and files', 'affected'), ('Candidate tests', 'tests')):
        lines += ['## ' + title, '']
        if not report[key]:
            lines += ['No current path found.', '']
        for node in report[key]:
            lines += [f"- **{escape(node['label'])}** — {node['category']}, {node['distance']} hop(s)"]
            for edge in node['explanation']:
                location = f" ({escape(edge['path'])}:{edge['line']})" if edge['path'] else ''
                identity = f" [{escape(edge['identity'])}]" if edge['identity'] else ''
                lines += [f"  - {escape(edge['source'])} → {escape(edge['target'])}: {edge['kind']} / {edge['origin']}{location}{identity}"]
        lines.append('')
    lines += ['## Historical associations', '']
    lines += [f"- {escape(n['path'])}: co-changed in {len(set(n['commits']))} sampled commit(s); not a dependency path."
              for n in report['associations']] or ['None in the requested history sample.']
    lines += ['', '## Coverage and limits', '',
              'Requested coverage: ' + ('complete within the stated adapters and budgets' if report['coverage']['complete'] else 'incomplete'), '']
    lines += ['- ' + escape(issue) for issue in report['coverage']['issues']]
    lines += ['- ' + escape(limit) for limit in report['limits']]
    lines.append('')
    return '\n'.join(lines)
