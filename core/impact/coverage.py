"""Offline actual coverage.py/V8 conversion; execution receipts are unsigned.

Borrow producer formats (coverage.py Apache-2.0, Node MIT). Adds explicit test
attribution and fresh selected-input binding, not a correctness assertion.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import time
from urllib.parse import urlparse
from urllib.request import url2pathname

from ..surface import TEST_NAME
from .build import build, safe_path, read_input
from .ingest import text

MAX_BYTES = 8 * 1024 * 1024


def _test(graph, value):
    if not isinstance(value, str) or 'file:' + value not in graph.nodes or not TEST_NAME.search(value):
        raise ValueError('test attribution must name a selected test file')
    return value


def _path(root, name):
    if not isinstance(name, str):
        raise ValueError('invalid producer path')
    # Actual coverage.py JSON uses native Windows separators. Normalize only
    # producer paths; receipt and observation paths retain strict POSIX rules.
    name = name.replace('\\', '/')
    candidate = Path(name)
    if candidate.is_absolute():
        try:
            name = candidate.resolve().relative_to(root).as_posix()
        except ValueError:
            return None  # External interpreter/dependency code is not an endpoint.
    safe_path(root, name)
    return name


def _python(root, graph, report, receipt, deadline):
    meta = report.get('meta', {})
    if (not isinstance(meta, dict) or meta.get('format') != 3 or meta.get('version') != '7.10.7'
            or meta.get('show_contexts') is not True):
        raise ValueError('qualified coverage.py format is 3 / 7.10.7 with contexts')
    mapping = receipt.get('contexts')
    if (not isinstance(mapping, dict) or not mapping or len(mapping) > 10000
            or any(not isinstance(k, str) or not k.strip() or len(k) > 500 for k in mapping)):
        raise ValueError('missing/invalid test contexts; empty contexts are unattributed')
    for test in mapping.values():
        _test(graph, test)
    files = report.get('files')
    if not isinstance(files, dict) or len(files) > 10000:
        raise ValueError('invalid coverage files')
    edges, issues, examined = set(), set(), 0
    for name, item in files.items():
        if time.monotonic() >= deadline:
            raise ValueError('coverage conversion deadline reached')
        path = _path(root, name)
        if path is None:
            continue
        if 'file:' + path not in graph.nodes:
            issues.add('covered project file is outside selected inputs: ' + path)
            continue
        if not isinstance(item, dict) or not isinstance(item.get('contexts'), dict):
            raise ValueError('missing coverage contexts')
        lines = item.get('executed_lines')
        source_lines = len(read_input(root, path, deadline).splitlines())
        if not isinstance(lines, list) or len(lines) > 100000 or any(type(n) is not int or not 1 <= n <= source_lines for n in lines):
            raise ValueError('invalid executed lines')
        contexts = item['contexts']
        for line in lines:
            if time.monotonic() >= deadline:
                raise ValueError('coverage conversion deadline reached')
            examined += 1
            if examined > 500000:
                raise ValueError('coverage line limit 500000 exceeded')
            labels = contexts.get(str(line), [])
            if not isinstance(labels, list) or len(labels) > 10000 or any(not isinstance(s, str) for s in labels):
                raise ValueError('invalid line contexts')
            if not labels:
                issues.add('coverage executed line has no attributed context')
            for label in labels:
                if label not in mapping:
                    issues.add('coverage includes unattributed contexts')
                    continue
                test = mapping[label]
                if test != path:
                    edges.add((test, path))
    return edges, issues


def _v8(root, graph, report, receipt, deadline):
    if not re.fullmatch(r'node-v8/22\.\d+\.\d+', receipt['producer']):
        raise ValueError('supported V8 producer is Node 22.x (local acceptance: 22.17.1)')
    test = _test(graph, receipt.get('test'))
    scripts = report.get('result')
    maps = report.get('source-map-cache', {})
    if not isinstance(scripts, list) or len(scripts) > 10000 or not isinstance(maps, dict):
        raise ValueError('invalid V8 script list/source maps')
    edges, issues, examined = set(), set(), 0
    for script in scripts:
        if time.monotonic() >= deadline:
            raise ValueError('coverage conversion deadline reached')
        if not isinstance(script, dict) or not isinstance(script.get('url'), str):
            raise ValueError('invalid V8 script')
        url = urlparse(script['url'])
        if url.scheme != 'file':
            continue
        if url.netloc not in ('', 'localhost'):
            raise ValueError('remote V8 file URL is unsupported')
        path = _path(root, url2pathname(url.path))
        if path is None:
            continue
        if 'file:' + path not in graph.nodes:
            issues.add('covered project script is outside selected inputs: ' + path)
            continue
        if script['url'] in maps or not path.endswith(('.js', '.mjs', '.cjs')):
            issues.add('source map or transformed script requires a qualified mapping: ' + path)
            continue
        source = read_input(root, path, deadline)
        length = len(source.decode('utf-8').encode('utf-16-le')) // 2
        functions = script.get('functions')
        if not isinstance(functions, list) or len(functions) > 100000:
            raise ValueError('invalid V8 functions')
        executed = False
        for function in functions:
            if not isinstance(function, dict) or not isinstance(function.get('ranges'), list):
                raise ValueError('invalid V8 ranges')
            for row in function['ranges']:
                if time.monotonic() >= deadline:
                    raise ValueError('coverage conversion deadline reached')
                examined += 1
                if examined > 500000 or not isinstance(row, dict):
                    raise ValueError('V8 range limit or invalid row')
                start, end, count = (row.get(k) for k in ('startOffset', 'endOffset', 'count'))
                if (any(type(v) is not int for v in (start, end, count))
                        or not 0 <= start <= end <= length or count < 0):
                    raise ValueError('V8 ranges do not fit fresh source')
                executed |= count > 0 and end > start
        if executed and test != path:
            edges.add((test, path))
    return edges, issues


def convert(root, kind, data, receipt, *, seconds=30):
    """Convert one explicit producer report. Never run tests or an engine.

    The caller collects and seals execution independently. A receipt is a local
    assertion and hash binding, not authentication of a fabricated producer.
    Incomplete conversions publish diagnostics and no active edges.
    """
    result = {'schema': 1, 'producer': 'impact-coverage/1', 'run': 'unqualified',
              'complete': False, 'source_fingerprint': '', 'edges': [], 'issues': [],
              'limits': ['Unsigned execution receipt; coverage is execution, not assertions.',
                         'Static context and isolated-run attribution are caller assertions.',
                         'V8 supports native JS source only; source maps remain unsupported.']}
    try:
        if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 0 <= seconds <= 300:
            raise ValueError('seconds must be finite and between 0 and 300')
        deadline = time.monotonic() + seconds
        root = Path(root).resolve(strict=True)
        if not isinstance(data, bytes) or len(data) > MAX_BYTES:
            raise ValueError('producer report exceeds 8 MiB or is not bytes')
        if not isinstance(receipt, dict) or type(receipt.get('schema')) is not int or receipt.get('schema') != 1:
            raise ValueError('invalid execution receipt')
        producer = text(receipt.get('producer'), 'producer')
        result['producer'] = 'impact-coverage/1 ' + producer
        result['run'] = text(receipt.get('run'), 'run')
        if (receipt.get('execution') != 'complete' or type(receipt.get('exit_code')) is not int
                or receipt['exit_code'] != 0 or type(receipt.get('passed')) is not int
                or receipt['passed'] <= 0 or type(receipt.get('failed')) is not int or receipt['failed'] != 0):
            raise ValueError('execution must have completed passing counted tests')
        if receipt.get('report_sha256') != hashlib.sha256(data).hexdigest():
            raise ValueError('producer report hash does not match execution receipt')
        report = json.loads(data)
        if not isinstance(report, dict):
            raise ValueError('invalid producer JSON')
        graph = build(root, seconds=max(0, deadline-time.monotonic()))
        result['source_fingerprint'] = graph.fingerprint
        if not graph.coverage.get('inputs_complete') or not graph.coverage.get('declarations_complete'):
            raise ValueError('current input/declaration coverage incomplete')
        if receipt.get('before') != graph.fingerprint or receipt.get('after') != graph.fingerprint:
            raise ValueError('execution inputs changed or receipt is stale')
        if kind == 'python':
            if producer != 'coverage.py/7.10.7':
                raise ValueError('qualified Python producer is coverage.py/7.10.7')
            relations, issues = _python(root, graph, report, receipt, deadline)
        elif kind == 'v8':
            relations, issues = _v8(root, graph, report, receipt, deadline)
        else:
            raise ValueError('unsupported coverage producer')
        # Re-read after conversion so native range reads cannot drift unnoticed.
        after = build(root, seconds=max(0, deadline-time.monotonic()))
        if after.fingerprint != graph.fingerprint or not after.coverage.get('inputs_complete'):
            raise ValueError('inputs changed during coverage conversion')
        if issues:
            result['issues'] = sorted(issues)
        elif not relations:
            result['issues'] = ['no attributed selected test-to-source execution found']
        else:
            result['edges'] = [{'source': 'file:' + a, 'target': 'file:' + b, 'kind': 'observed_test'}
                               for a, b in sorted(relations)]
            result['complete'] = True
        result['receipt'] = {'producer': producer, 'report_sha256': receipt['report_sha256'],
                             'passed': receipt['passed'], 'failed': receipt['failed']}
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        result['issues'] = [str(exc)]
    return result
