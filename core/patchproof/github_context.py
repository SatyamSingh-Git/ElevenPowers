"""GitHub subject metadata is data, not a command or independent attestation."""
import json
import math
from pathlib import Path
import re

MAX_EVENT_BYTES = 2 * 1024 * 1024


def repository(value):
    if not isinstance(value, str) or not re.fullmatch(
            r'[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}', value):
        raise ValueError('repository must be a GitHub owner/name')
    if value.rsplit('/', 1)[1] in {'.', '..'}:
        raise ValueError('invalid repository name')
    return value


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('duplicate event field')
        result[key] = value
    return result


def _shape(value):
    pending, count = [(value, 0)], 0
    while pending:
        item, depth = pending.pop()
        count += 1
        if depth > 64 or count > 100000:
            raise ValueError('event structure limit exceeded')
        if isinstance(item, dict):
            if any(not isinstance(k, str) for k in item):
                raise ValueError('event keys must be strings')
            pending.extend((v, depth + 1) for v in item.values())
        elif isinstance(item, list):
            pending.extend((v, depth + 1) for v in item)
        elif isinstance(item, float) and not math.isfinite(item):
            raise ValueError('event numbers must be finite')
        elif item is not None and not isinstance(item, (str, int, float, bool)):
            raise ValueError('unsupported event value')


def read_event(path):
    path = Path(path)
    if path.is_symlink() or path.resolve() != path.absolute():
        raise ValueError('linked event input is unavailable')
    try:
        with path.open('rb') as stream:
            data = stream.read(MAX_EVENT_BYTES + 1)
        if len(data) > MAX_EVENT_BYTES:
            raise ValueError('event byte limit exceeded')
        value = json.loads(data, object_pairs_hook=_pairs)
        _shape(value)
        if not isinstance(value, dict):
            raise ValueError('event must be an object')
        return value
    except (RecursionError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('event JSON is unavailable') from error


def _sha(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', value) or not int(value, 16):
        raise ValueError('event requires full nonzero commit IDs')
    return value


def declared(repo, event=None):
    repo = repository(repo)
    value = {'repository': repo, 'head_repository': repo, 'pull_request': None,
             'expected_base': None, 'expected_head': None, 'issues': []}
    if event is None:
        return value
    _shape(event)
    if not isinstance(event, dict):
        raise ValueError('event must be an object')
    try:
        if 'repository' in event and repository(event['repository']['full_name']).casefold() != repo.casefold():
            raise ValueError('event repository does not match declared repository')
        if 'pull_request' in event:
            pr = event['pull_request']
            if repository(pr['base']['repo']['full_name']).casefold() != repo.casefold():
                raise ValueError('PR base repository does not match declared repository')
            number = event['number']
            if type(number) is not int or not 0 < number < 2**63:
                raise ValueError('invalid PR number')
            head_repo = pr['head'].get('repo')
            value.update(pull_request=number, expected_base=_sha(pr['base']['sha']),
                         expected_head=_sha(pr['head']['sha']),
                         head_repository=repository(head_repo['full_name']) if head_repo else None)
            if not head_repo:
                value['issues'].append('PR head repository metadata is unavailable')
        return value
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError('event subject metadata is incomplete') from error


def artifact_link(repo, run_id, url):
    repo = repository(repo)
    if not isinstance(run_id, str) or not re.fullmatch(r'[1-9][0-9]{0,19}', run_id):
        raise ValueError('artifact link requires a positive run ID')
    pattern = (r'https://github\.com/'+re.escape(repo)+'/actions/runs/'
               +run_id+r'/artifacts/[1-9][0-9]{0,19}')
    if not isinstance(url, str) or not re.fullmatch(pattern, url, re.IGNORECASE):
        raise ValueError('artifact URL does not match repository and run')
    return '[Download the evidence artifact]('+url+')'


