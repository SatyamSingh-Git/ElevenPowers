"""Candidate behavior only. The parent controller owns every assertion."""
import contextlib
import io
import json
from pathlib import Path
import sys


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
        responses.append(response)
    return {'responses': responses}


if __name__ == '__main__':
    with contextlib.redirect_stdout(OutputSink()):
        value = main(Path(sys.argv[1]).resolve(), json.loads(sys.argv[2]))
    print(json.dumps(value, allow_nan=False))
