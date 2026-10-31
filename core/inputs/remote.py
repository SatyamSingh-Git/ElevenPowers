"""Explicit, approved observations of declared remote resources; reports never probe.

A project declares the URLs its checks depend on in ``elevenpowers.remotes.json``.
Only a local, Git-untracked approval of the exact declared URL lets the explicit
``observe`` action fetch it; a tracked declaration cannot grant network access.
Each observation records the SHA-256 of the identity-encoded response body, its
status and selected validators, and is appended to bounded local history.

Everything else is offline. Status compares recorded observations; a receipt is
associated with the complete observations that bracket its timestamp. A remote
is never called fresh: the newest observation has an age, and two equal digests
cannot exclude a change that reverted between them. A CDN cache can also serve
bytes older than the origin, which ``cache_control`` records but cannot measure.

Borrowed: Python's standard-library ``urllib`` client (PSF licence) and the HTTP
validator fields of RFC 9110. Added: approval-gated observation, recorded
history and time-bracketed receipt association, all readable without a network.
"""
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import math
import time
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

from ..jobs import ledger_write
from ..redact import scrub
from . import bindings, definition

FILE = 'elevenpowers.remotes.json'
APPROVALS = 'remote-approvals.json'
HISTORY = 'remote-observations.json'
MAX_REMOTES = 16
PER_REMOTE = 64
DEFAULTS = {'bytes': 8 * 1024 * 1024, 'seconds': 15}
AGENT = 'ElevenPowers-remote-observation/1'
LIMITS = [
    'Observations are explicit, local and unsigned; reports and status never contact the network.',
    'A remote is never fresh: the newest observation has an age, and equal digests cannot exclude a reverted change between them.',
    'Responses may come from a CDN or proxy cache; cache_control is recorded, not measured.',
    'Receipt association compares timestamps from the same local clock and does not prove the check read this resource.',
    'Only identity-encoded response bytes are digested; headers, authentication and server state are not.',
]


def _loopback(host):
    if host == 'localhost':
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def url(value):
    """A declared URL must be literal, credential-free and https unless loopback."""
    if not isinstance(value, str) or not value or len(value) > 2048 or not value.isascii():
        raise ValueError('remote URL must be ASCII text up to 2048 characters')
    if any(c.isspace() or c == '\0' for c in value):
        raise ValueError('remote URL cannot contain whitespace')
    parts = urllib.parse.urlsplit(value)
    if parts.scheme not in ('https', 'http') or not parts.hostname:
        raise ValueError('remote URL must be absolute http(s)')
    if parts.scheme == 'http' and not _loopback(parts.hostname):
        raise ValueError('plain http is supported only for loopback hosts')
    if parts.username is not None or parts.password is not None or '@' in parts.netloc:
        raise ValueError('credential-bearing remote URLs are unsupported')
    if parts.fragment:
        raise ValueError('remote URL fragments are unsupported')
    if scrub(value) != value or 'REDACTED' in value:
        raise ValueError('remote URLs carrying credentials are unsupported')
    return value


def load(root):
    data = definition.raw(Path(root) / FILE, optional=True)
    if data is None:
        return None
    value = definition.decode(data)
    if (not isinstance(value, dict) or set(value) - {'schema', 'remotes', 'limits'}
            or type(value.get('schema')) is not int or value['schema'] != 1
            or not isinstance(value.get('remotes'), list)
            or not 1 <= len(value['remotes']) <= MAX_REMOTES):
        raise ValueError('unsupported remote declaration')
    seen = set()
    for remote in value['remotes']:
        if not isinstance(remote, dict) or set(remote) != {'id', 'url'}:
            raise ValueError('unsupported remote entry')
        name = definition.label(remote['id'])
        if name in seen:
            raise ValueError('duplicate remote label')
        seen.add(name)
        url(remote['url'])
    limits = value.get('limits', {})
    if not isinstance(limits, dict) or set(limits) - set(DEFAULTS):
        raise ValueError('unsupported remote limits')
    limits = {**DEFAULTS, **limits}
    if (type(limits['bytes']) is not int or not 1 <= limits['bytes'] <= 64 * 1024 * 1024
            or type(limits['seconds']) not in (int, float) or not math.isfinite(limits['seconds'])
            or not 0 < limits['seconds'] <= 60):
        raise ValueError('remote limits exceed supported finite ranges')
    return {**value, 'limits': limits, '_digest': hashlib.sha256(data).hexdigest()}


def _state_path(root, name):
    path = Path(root) / '.elevenpowers' / name
    if path.resolve() != path.absolute() or path.is_symlink():
        raise ValueError('linked remote observation state is unsupported')
    return path


def _private_state(root, name, kind):
    """Read one private state file bound to this project, or None when absent."""
    data = definition.raw(_state_path(root, name), 4 * 1024 * 1024, optional=True)
    if data is None:
        return None
    value = definition.decode(data)
    if (not isinstance(value, dict) or set(value) != {'schema', 'project', kind}
            or type(value['schema']) is not int or value['schema'] != 1
            or value['project'] != bindings.identity(root)):
        raise ValueError('remote state is malformed or belongs to another project')
    return value


def approvals(root, deadline):
    bindings.private(root, deadline, APPROVALS)
    value = _private_state(root, APPROVALS, 'remotes')
    if value is None:
        return {}
    if not isinstance(value['remotes'], dict) or len(value['remotes']) > MAX_REMOTES:
        raise ValueError('remote approval is malformed')
    for name, approved in value['remotes'].items():
        definition.label(name)
        url(approved)
    return value['remotes']


def history(root):
    value = _private_state(Path(root).resolve(strict=True), HISTORY, 'observations')
    if value is None:
        return []
    rows = value['observations']
    if not isinstance(rows, list) or len(rows) > MAX_REMOTES * PER_REMOTE:
        raise ValueError('remote observation history is malformed')
    for row in rows:
        if (not isinstance(row, dict) or not isinstance(row.get('id'), str)
                or type(row.get('at')) not in (int, float) or not math.isfinite(row['at'])
                or row.get('state') not in ('complete', 'incomplete')
                or row['state'] == 'complete' and not (isinstance(row.get('digest'), str)
                                                       and len(row['digest']) == 64)):
            raise ValueError('remote observation row is malformed')
    return rows


def _ignore(root, names):
    ignored = _state_path(root, '.gitignore')
    prior = definition.raw(ignored, optional=True)
    # A new marker ignores the whole directory, as the ledger's own does; later
    # ledger saves see an existing marker and would not add that rule themselves.
    text = '*\n' if prior is None else prior.decode('utf-8')
    if text == '*\n' and prior is not None:
        return
    missing = [f'/{n}\n' for n in names if f'/{n}\n' not in text and text != '*\n']
    if prior is None:
        bindings._write(ignored, text.encode())
        return
    if missing:
        text += ('\n' if text and not text.endswith('\n') else '') + ''.join(missing)
        bindings._write(ignored, text.encode())


def approve(root, name):
    """Approve the exact URL the project currently declares for ``name``."""
    root = Path(root).resolve(strict=True)
    declaration = load(root)
    declared = {r['id']: r['url'] for r in (declaration or {}).get('remotes', [])}
    if name not in declared:
        raise ValueError('remote label is not declared by this project')
    bindings.private(root, time.monotonic() + 5, APPROVALS)
    _state_path(root, APPROVALS).parent.mkdir(exist_ok=True)
    with ledger_write(root):
        current = _private_state(root, APPROVALS, 'remotes') or {
            'schema': 1, 'project': bindings.identity(root), 'remotes': {}}
        current['remotes'][name] = declared[name]
        _ignore(root, [APPROVALS, HISTORY, '.gitignore', 'ledger.lock'])
        bindings._write(_state_path(root, APPROVALS),
                        json.dumps(current, ensure_ascii=True, indent=2).encode())
    return {'id': name, 'state': 'approved'}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # A redirect target was never approved.


def _fetch(target, limits):
    started = time.monotonic()
    row = {'status': None, 'digest': None, 'bytes': 0, 'etag': None, 'last_modified': None,
           'content_type': None, 'cache_control': None, 'issue': ''}
    scheme = urllib.parse.urlsplit(target).scheme
    row['via_proxy'] = scheme in urllib.request.getproxies()
    opener = urllib.request.build_opener(_NoRedirect)
    request = urllib.request.Request(target, headers={'User-Agent': AGENT, 'Accept-Encoding': 'identity'})
    try:
        with opener.open(request, timeout=limits['seconds']) as response:
            row['status'] = response.status
            headers = response.headers
            for key, field in (('etag', 'ETag'), ('last_modified', 'Last-Modified'),
                               ('content_type', 'Content-Type'), ('cache_control', 'Cache-Control')):
                row[key] = (headers.get(field) or '')[:256] or None
            encoding = (headers.get('Content-Encoding') or 'identity').strip().lower()
            declared = headers.get('Content-Length')
            if encoding != 'identity':
                row['issue'] = 'response is content-encoded; identity bytes were not observed'
            elif declared and declared.isdigit() and int(declared) > limits['bytes']:
                row['issue'] = 'declared response size exceeds the observation byte limit'
            else:
                digest, total = hashlib.sha256(), 0
                while True:
                    if time.monotonic() - started > limits['seconds']:
                        row['issue'] = 'observation deadline reached while reading'
                        break
                    chunk = response.read(min(65536, limits['bytes'] - total + 1))
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > limits['bytes']:
                        row['issue'] = 'response exceeds the observation byte limit'
                        break
                    digest.update(chunk)
                row['bytes'] = total
                if not row['issue'] and declared and declared.isdigit() and int(declared) != total:
                    row['issue'] = 'response ended before its declared length'
                if not row['issue']:
                    row['digest'] = digest.hexdigest()
    except urllib.error.HTTPError as error:
        row['status'] = error.code
        row['issue'] = ('redirect was not followed; its target is not approved'
                        if 300 <= error.code < 400 else f'HTTP status {error.code}')
        error.close()
    except (urllib.error.URLError, OSError, ValueError) as error:
        reason = getattr(error, 'reason', error)
        row['issue'] = 'remote unavailable: ' + type(reason).__name__
    if row['digest'] is None and not row['issue']:
        row['issue'] = 'no complete response body was observed'
    row['elapsed_ms'] = round((time.monotonic() - started) * 1000, 3)
    return row


def observe(root, names=None, *, seconds=None):
    """Fetch approved declared remotes now and append the results to history."""
    root = Path(root).resolve(strict=True)
    declaration = load(root)
    if declaration is None:
        raise ValueError('this project declares no remote resources')
    limits = dict(declaration['limits'])
    if seconds is not None:
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 0 < seconds <= 60:
            raise ValueError('observation seconds outside finite range')
        limits['seconds'] = min(limits['seconds'], seconds)
    approved = approvals(root, time.monotonic() + 5)
    declared = {r['id']: r['url'] for r in declaration['remotes']}
    selected = list(declared) if names is None else list(names)
    rows = []
    for name in selected:
        if name not in declared:
            raise ValueError('remote label is not declared by this project')
        base = {'id': name, 'url': declared[name]}
        if approved.get(name) != declared[name]:
            reason = 'not approved' if name not in approved else 'declared URL differs from its approval'
            rows.append({**base, 'state': 'refused', 'issue': reason})
            continue  # No request is made for an unapproved or changed URL.
        at = time.time()
        fetched = _fetch(declared[name], limits)
        rows.append({**base, **fetched, 'at': at,
                     'observed_at': datetime.fromtimestamp(at, timezone.utc).isoformat(),
                     'state': 'complete' if fetched['digest'] else 'incomplete'})
    recorded = [r for r in rows if r['state'] != 'refused']
    if recorded:
        with ledger_write(root):
            existing = history(root)
            combined = existing + recorded
            kept = []
            for name in {r['id'] for r in combined}:
                own = [r for r in combined if r['id'] == name]
                kept += own[-PER_REMOTE:]
            kept.sort(key=lambda r: r['at'])
            _ignore(root, [APPROVALS, HISTORY, '.gitignore', 'ledger.lock'])
            bindings._write(_state_path(root, HISTORY), json.dumps(
                {'schema': 1, 'project': bindings.identity(root), 'observations': kept},
                ensure_ascii=True, indent=2).encode())
    return rows


def associate(rows, name, at):
    """Bracket one receipt timestamp with complete observations of one remote."""
    complete = [r for r in rows if r['id'] == name and r['state'] == 'complete']
    before = max((r for r in complete if r['at'] <= at), key=lambda r: r['at'], default=None)
    after = min((r for r in complete if r['at'] > at), key=lambda r: r['at'], default=None)
    latest = max(complete, key=lambda r: r['at'], default=None)
    if before and after:
        state = 'unchanged-around-run' if before['digest'] == after['digest'] else 'changed-around-run'
    elif before:
        state = 'observed-before-run-only'
    elif after:
        state = 'observed-after-run-only'
    else:
        state = 'unobserved'
    reference = before or after
    since = None
    if reference and latest:
        since = 'unchanged-as-of-latest' if latest['digest'] == reference['digest'] else 'changed-since-run'
    return {'remote': name, 'association': state, 'since_run': since,
            'before_digest': before['digest'] if before else None,
            'after_digest': after['digest'] if after else None,
            'latest_observed_at': latest['observed_at'] if latest else None}


def status(root, *, now=None, deadline=None):
    """Summarise declared remotes from local state only."""
    root = Path(root).resolve(strict=True)
    try:
        declaration = load(root)
    except (OSError, ValueError) as error:
        return {'schema': 1, 'state': 'incomplete', 'remotes': [], 'issues': [definition_issue(error)],
                'limits': list(LIMITS)}
    if declaration is None:
        return {'schema': 1, 'state': 'not_configured', 'remotes': [], 'issues': [], 'limits': list(LIMITS)}
    now = time.time() if now is None else now
    issues = []
    try:
        approved = approvals(root, deadline if deadline is not None else time.monotonic() + 5)
    except (OSError, ValueError, TimeoutError) as error:
        approved, issues = {}, [definition_issue(error)]
    try:
        rows = history(root)
    except (OSError, ValueError) as error:
        rows, issues = [], issues + [definition_issue(error)]
    remotes = []
    for remote in declaration['remotes']:
        name, target = remote['id'], remote['url']
        own = [r for r in rows if r['id'] == name and r.get('url') == target]
        complete = [r for r in own if r['state'] == 'complete']
        latest = own[-1] if own else None
        entry = {'id': name, 'url': target,
                 'approval': ('approved' if approved.get(name) == target else
                              'url-changed' if name in approved else 'not-approved'),
                 'observations': len(own), 'latest_state': latest['state'] if latest else None,
                 'latest_observed_at': latest['observed_at'] if latest else None,
                 'latest_status': latest.get('status') if latest else None,
                 'latest_issue': latest.get('issue') if latest else None,
                 'digest': complete[-1]['digest'] if complete else None,
                 'age_seconds': round(now - complete[-1]['at'], 3) if complete else None,
                 'cache_control': complete[-1].get('cache_control') if complete else None,
                 'changed': (complete[-1]['digest'] != complete[-2]['digest']) if len(complete) > 1 else None}
        if entry['approval'] != 'approved':
            entry['state'] = entry['approval']
        elif not own:
            entry['state'] = 'never-observed'
        elif latest['state'] != 'complete':
            entry['state'] = 'incomplete'
        else:
            entry['state'] = 'changed' if entry['changed'] else 'observed'
        remotes.append(entry)
    state = 'incomplete' if issues else 'available'
    return {'schema': 1, 'state': state, 'remotes': remotes, 'issues': issues, 'limits': list(LIMITS),
            '_rows': rows}


def definition_issue(error):
    if isinstance(error, ValueError):
        return 'ValueError: ' + str(error)[:192]
    return type(error).__name__ + ': remote observation state unavailable'


def receipts_view(value, receipts):
    """Associate each receipt with every declared remote, using recorded history."""
    rows = value.pop('_rows', [])
    if value['state'] == 'not_configured':
        return value
    current = {r['id']: r['url'] for r in value['remotes']}
    rows = [r for r in rows if current.get(r['id']) == r.get('url')]
    value['associations'] = [{'receipt_key': receipt['receipt_key'], **associate(rows, name, receipt['recorded_at'])}
                             for receipt in receipts for name in current]
    return value


def markdown(value):
    from ..export import _text
    lines = ['## Remote observations', '']
    if value['state'] == 'not_configured':
        return lines + ['No remote resources are declared.', '']
    lines += [f"State: {_text(value['state'])}.", '',
              '| Remote | Approval | State | Latest observation | Age (s) | Changed |', '|---|---|---|---|---|---|']
    for r in value['remotes']:
        cells = [r['id'], r['approval'], r['state'], r['latest_observed_at'] or '—',
                 '—' if r['age_seconds'] is None else r['age_seconds'],
                 '—' if r['changed'] is None else ('yes' if r['changed'] else 'no')]
        lines.append('| ' + ' | '.join(_text(c) for c in cells) + ' |')
    for a in value.get('associations', []):
        lines.append(f"- Receipt {_text(a['receipt_key'][:12])} · {_text(a['remote'])}: "
                     f"{_text(a['association'])}; since run: {_text(a['since_run'] or 'unknown')}")
    lines += ['- ' + _text(i) for i in value['issues']]
    lines += ['- ' + _text(limit) for limit in value['limits']] + ['']
    return lines
