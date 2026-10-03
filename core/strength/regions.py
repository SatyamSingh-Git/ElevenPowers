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
    return function_targets(functions, changed)


def function_targets(functions, changed):
    """Expand narrow hunks, partition broad hunks and retain module gaps."""
    targets = []
    for region in changed:
        enclosing = [f for f in functions if f[0] <= region[0] and f[1] >= region[1]]
        if enclosing:
            chosen = [min(enclosing, key=lambda f: f[1]-f[0])]
            chosen.extend(f for f in functions if region[0] <= f[0] <= f[1] <= region[1])
        else:
            chosen = [f for f in functions if overlap(f[0], f[1], region)]
        targets.extend(chosen)
        cursor = region[0]
        for start, end, _ in sorted(chosen):
            if cursor < start:
                targets.append((cursor, min(start-1, region[1]), 'module'))
            cursor = max(cursor, end+1)
        if cursor <= region[1]:
            targets.append((cursor, region[1], 'module'))
    return sorted(set(targets))


def location(start, end, changed, targets):
    choices = [t for t in targets if t[0] <= start <= end <= t[1]]
    if not choices:
        return None
    target = min(choices, key=lambda t: t[1]-t[0])
    relevance = 'changed_lines' if any(overlap(start,end,r) for r in changed) else 'changed_function'
    return relevance, target[2], target
