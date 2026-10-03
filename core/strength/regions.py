"""Changed line attribution and Python function expansion, with no optional imports."""
import ast


def validate(regions, paths):
    if not isinstance(regions, dict) or set(regions) != set(paths):
        raise ValueError('changed regions must cover exactly the selected paths')
    count = 0
    for ranges in regions.values():
        if not isinstance(ranges, list):
            raise ValueError('invalid changed ranges')
        count += len(ranges)
        for item in ranges:
            if not isinstance(item, list) or len(item) != 2 or any(type(n) is not int for n in item) or not 1 <= item[0] <= item[1] <= 1000000:
                raise ValueError('invalid changed line range')
    if count > 2048:
        raise ValueError('changed-region limit exceeded')


def overlap(start, end, region):
    return start <= region[1] and end >= region[0]


def python_targets(source, changed):
    tree = ast.parse(source)
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            functions.append((start, node.end_lineno, node.name))
    targets = []
    for region in changed:
        enclosing = [f for f in functions if f[0] <= region[0] and f[1] >= region[1]]
        if enclosing:
            targets.append(min(enclosing, key=lambda f: f[1]-f[0]))
        else:
            targets.append((*region, 'module'))
    return sorted(set(targets))


def location(start, end, changed, targets):
    choices = [t for t in targets if overlap(start, end, t)]
    if not choices:
        return None
    target = min(choices, key=lambda t: t[1]-t[0])
    relevance = 'changed_lines' if any(overlap(start,end,r) for r in changed) else 'changed_function'
    return relevance, target[2], target
