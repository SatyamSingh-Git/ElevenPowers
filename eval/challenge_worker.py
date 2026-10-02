"""Candidate behavior only. The parent controller owns every assertion."""
import contextlib
import json
from pathlib import Path
import sys


def encode(value):
    """Bounded, type-preserving behavior; dictionary order is immaterial."""
    remaining = 10000
    def visit(item, depth):
        nonlocal remaining
        remaining -= 1
        if remaining < 0 or depth > 16:
            raise ValueError('candidate behavior exceeds structural limit')
        kind = type(item)
        if item is None:
            return ['none']
        if kind in (bool, int, float, str):
            if kind is str and len(item.encode('utf-8')) > 512*1024:
                raise ValueError('candidate behavior exceeds string limit')
            return [kind.__name__, item]
        if kind in (list, tuple):
            return [kind.__name__, [visit(child, depth + 1) for child in item]]
        if kind is dict:
            pairs = [[visit(key, depth + 1), visit(child, depth + 1)] for key, child in item.items()]
            pairs.sort(key=lambda pair: json.dumps(pair[0], allow_nan=False))
            return ['dict', pairs]
        return ['unsupported']
    return visit(value, 0)


class OutputSink:
    def __init__(self):
        self.bytes = 0

    def write(self, value):
        self.bytes += len(value.encode('utf-8'))
        if self.bytes > 8*1024*1024:
            raise ValueError('candidate output exceeds limit')
        return len(value)

    def flush(self):
        pass


def main(root, requests):
    files = [p for p in (root / 'bank').rglob('*.py') if '__pycache__' not in p.parts]
    if len(files) > 32:
        raise ValueError('candidate package exceeds file limit')
    package_bytes = 0
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('candidate package escapes root')
        package_bytes += path.stat().st_size
        if package_bytes > 512*1024:
            raise ValueError('candidate package exceeds byte limit')
    sys.path.insert(0, str(root))
    from bank.engine import apply_batch
    from bank.view import total, statement
    responses = []
    for request in requests:
        b = request['balances']
        response = {'result': None, 'exception': ''}
        if request['operation'] == 'apply':
            j = {key: tuple(value) for key, value in request['journal'].items()}
            try:
                response['result'] = apply_batch(b, j, request['entries'])
            except Exception as exc:
                response['exception'] = type(exc).__name__
            response.update(balances=b, journal=j)
        else:
            try:
                response['result'] = (total if request['operation'] == 'total' else statement)(b)
            except Exception as exc:
                response['exception'] = type(exc).__name__
        responses.append(encode(response))
    return {'responses': responses}


if __name__ == '__main__':
    with contextlib.redirect_stdout(OutputSink()):
        value = main(Path(sys.argv[1]).resolve(), json.loads(sys.argv[2]))
    print(json.dumps(value, allow_nan=False))
