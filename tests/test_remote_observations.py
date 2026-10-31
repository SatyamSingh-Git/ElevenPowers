"""Remote observation controls, each read forward and adversarially.

A loopback HTTP server stands in for the remote. It counts every request, so a
control can show that a refused, redirected or report-only path made no request.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest

from core.inputs import remote
from core.ledger import Ledger
from tests.test_patchproof_identity import git, commit
from tests.test_patchproof_report import seed

SCRIPT = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_inputs.py'


class Server:
    """Routes map a path to (status, headers, body, delay); hits counts requests."""

    def __init__(self):
        self.routes, self.hits = {}, {}
        owner = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.0'

            def do_GET(self):
                owner.hits[self.path] = owner.hits.get(self.path, 0) + 1
                status, headers, body, delay = owner.routes.get(self.path, (404, {}, b'missing', 0))
                time.sleep(delay)
                self.send_response(status)
                for key, value in headers.items():
                    self.send_header(key, value)
                if 'Content-Length' not in headers and headers.get('X-Omit-Length') is None:
                    self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                try:
                    self.wfile.write(body)
                except OSError:
                    pass

            def log_message(self, *args):
                pass

        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.base = f'http://127.0.0.1:{self.httpd.server_address[1]}'
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def route(self, path, body=b'', status=200, headers=None, delay=0):
        self.routes[path] = (status, headers or {}, body, delay)
        return self.base + path


@pytest.fixture
def server():
    value = Server()
    yield value
    value.httpd.shutdown()
    value.httpd.server_close()


@pytest.fixture
def project(tmp_path):
    root = tmp_path / 'project'
    root.mkdir()
    git(root, 'init', '-q')
    git(root, 'config', 'core.autocrlf', 'false')
    return root


def declare(root, *remotes, limits=None):
    value = {'schema': 1, 'remotes': [{'id': name, 'url': target} for name, target in remotes]}
    if limits:
        value['limits'] = limits
    (root / remote.FILE).write_text(json.dumps(value), encoding='utf-8')


# Declarations

@pytest.mark.parametrize('target', ['https://example.invalid/schema.json',
                                    'http://127.0.0.1:9/x', 'http://localhost/x', 'http://[::1]/x'])
def test_https_and_loopback_urls_are_accepted(target):
    assert remote.url(target) == target


@pytest.mark.parametrize('target', [
    'http://example.com/x', 'ftp://example.com/x', 'file:///etc/passwd', '//example.com/x',
    'https://user:secret@example.com/x', 'https://example.com/x#part', 'https://example.com/ x',
    'https://example.com/x?token=ghp_' + 'A' * 30, 'https://exämple.com/x', 'https://' + 'a' * 2050])
def test_unsafe_or_credential_urls_are_refused(target):
    with pytest.raises(ValueError):
        remote.url(target)


def test_declaration_is_strict(project):
    declare(project, ('schema', 'https://example.invalid/a'))
    assert remote.load(project)['limits'] == remote.DEFAULTS
    for bad in ({'schema': 2, 'remotes': [{'id': 'a', 'url': 'https://example.invalid/a'}]},
                {'schema': 1, 'remotes': []},
                {'schema': 1, 'remotes': [{'id': 'a', 'url': 'https://example.invalid/a', 'extra': 1}]},
                {'schema': 1, 'remotes': [{'id': 'a', 'url': 'https://example.invalid/a'}] * 2},
                {'schema': 1, 'remotes': [{'id': 'a', 'url': 'https://example.invalid/a'}],
                 'limits': {'seconds': 0}}):
        (project / remote.FILE).write_text(json.dumps(bad), encoding='utf-8')
        with pytest.raises(ValueError):
            remote.load(project)


# Approval gates every request

def test_only_a_local_approval_of_the_exact_declared_url_can_fetch(project, server):
    target = server.route('/schema.json', b'{"v":1}')
    declare(project, ('schema', target))
    refused = remote.observe(project)
    assert refused[0]['state'] == 'refused' and server.hits == {}
    remote.approve(project, 'schema')
    assert remote.observe(project)[0]['state'] == 'complete' and server.hits == {'/schema.json': 1}
    # The tracked declaration changes the URL; the old approval does not follow it.
    declare(project, ('schema', server.route('/other.json', b'other')))
    changed = remote.observe(project)
    assert changed[0]['state'] == 'refused' and 'differs' in changed[0]['issue']
    assert '/other.json' not in server.hits
    assert remote.status(project)['remotes'][0]['approval'] == 'url-changed'
    with pytest.raises(ValueError):
        remote.approve(project, 'undeclared')


def test_tracked_or_copied_approval_is_not_local_approval(project, server, tmp_path):
    declare(project, ('schema', server.route('/s', b'x')))
    remote.approve(project, 'schema')
    git(project, 'add', '-f', '.elevenpowers/' + remote.APPROVALS)
    with pytest.raises(ValueError, match='tracked'):
        remote.observe(project)
    git(project, 'rm', '-q', '--cached', '.elevenpowers/' + remote.APPROVALS)
    other = tmp_path / 'other'
    other.mkdir()
    git(other, 'init', '-q')
    declare(other, ('schema', server.base + '/s'))
    (other / '.elevenpowers').mkdir()
    (other / '.elevenpowers' / remote.APPROVALS).write_bytes(
        (project / '.elevenpowers' / remote.APPROVALS).read_bytes())
    with pytest.raises(ValueError, match='another project'):
        remote.observe(other)
    assert server.hits == {}


# What an observation records

def test_digest_is_the_body_sha256_and_a_change_is_detected(project, server):
    target = server.route('/api.json', b'{"version": 1}', headers={'ETag': '"v1"', 'Cache-Control': 'max-age=60'})
    declare(project, ('api', target))
    remote.approve(project, 'api')
    first = remote.observe(project)[0]
    assert first['digest'] == hashlib.sha256(b'{"version": 1}').hexdigest()
    assert (first['etag'], first['cache_control'], first['bytes']) == ('"v1"', 'max-age=60', 14)
    remote.observe(project)
    same = remote.status(project)['remotes'][0]
    assert (same['state'], same['changed'], same['observations']) == ('observed', False, 2)
    server.route('/api.json', b'{"version": 2}', headers={'ETag': '"v1"'})  # A stale validator.
    remote.observe(project)
    changed = remote.status(project)['remotes'][0]
    assert (changed['state'], changed['changed']) == ('changed', True)
    assert changed['digest'] == hashlib.sha256(b'{"version": 2}').hexdigest()


def test_a_redirect_is_recorded_and_its_target_is_never_requested(project, server):
    server.route('/target', b'secret')
    declare(project, ('moved', server.route('/moved', status=302, headers={'Location': server.base + '/target'})))
    remote.approve(project, 'moved')
    row = remote.observe(project)[0]
    assert (row['state'], row['status'], row['digest']) == ('incomplete', 302, None)
    assert 'redirect' in row['issue'] and '/target' not in server.hits


@pytest.mark.parametrize(('route', 'needle'), [
    (dict(status=404, body=b'missing'), 'HTTP status 404'),
    (dict(body=b'x' * 100, headers={'Content-Length': '100'}), 'declared response size'),
    (dict(body=b'x' * 100, headers={'X-Omit-Length': '1'}), 'exceeds the observation byte limit'),
    (dict(body=b'short', headers={'Content-Length': '50'}), 'before its declared length'),
    (dict(body=b'zz', headers={'Content-Encoding': 'gzip'}), 'content-encoded'),
    (dict(body=b'late', delay=3), 'unavailable'),
])
def test_failures_and_limits_are_incomplete_never_a_digest(project, server, route, needle):
    declare(project, ('r', server.route('/r', **route)), limits={'bytes': 64, 'seconds': 1})
    remote.approve(project, 'r')
    row = remote.observe(project)[0]
    assert row['state'] == 'incomplete' and row['digest'] is None, row
    assert needle in row['issue'], row['issue']
    assert remote.status(project)['remotes'][0]['state'] == 'incomplete'


def test_history_is_bounded_per_remote(project, server, monkeypatch):
    monkeypatch.setattr(remote, 'PER_REMOTE', 3)
    declare(project, ('a', server.route('/a', b'a')), ('b', server.route('/b', b'b')))
    remote.approve(project, 'a')
    remote.approve(project, 'b')
    remote.observe(project, ['b'])
    for _ in range(5):
        remote.observe(project, ['a'])
    rows = remote.history(project)
    assert [r['id'] for r in rows].count('a') == 3 and [r['id'] for r in rows].count('b') == 1


def test_state_directory_ignores_itself_including_later_ledger_state(project, server):
    declare(project, ('a', server.route('/a', b'a')))
    remote.approve(project, 'a')
    remote.observe(project)
    Ledger(root=project, task='t', request='private').save()
    assert git(project, 'status', '--porcelain').decode().strip() == '?? ' + remote.FILE


# Offline reading

def test_status_and_bundles_never_contact_the_network(project, server, monkeypatch):
    declare(project, ('api', server.route('/api', b'v1')))
    remote.approve(project, 'api')
    remote.observe(project)
    hits = dict(server.hits)

    def forbidden(*args, **kwargs):
        raise AssertionError('a read path contacted the network')

    monkeypatch.setattr(remote, '_fetch', forbidden)
    monkeypatch.setattr('urllib.request.OpenerDirector.open', forbidden)
    assert remote.status(project)['remotes'][0]['state'] == 'observed'
    commit(project, 'declare')
    from core.patchproof.report import build
    value = build(project, 'HEAD', 'HEAD')
    assert value['remote_observations']['remotes'][0]['id'] == 'api'
    assert server.hits == hits


def test_receipts_are_associated_by_the_observations_that_bracket_them():
    a, b = 'a' * 64, 'b' * 64
    rows = [{'id': 'r', 'state': 'complete', 'at': 10, 'digest': a, 'observed_at': 't10'},
            {'id': 'r', 'state': 'incomplete', 'at': 15, 'digest': None, 'observed_at': 't15'},
            {'id': 'r', 'state': 'complete', 'at': 20, 'digest': a, 'observed_at': 't20'},
            {'id': 'r', 'state': 'complete', 'at': 30, 'digest': b, 'observed_at': 't30'}]
    around = remote.associate(rows, 'r', 12)
    assert (around['association'], around['since_run']) == ('unchanged-around-run', 'changed-since-run')
    assert remote.associate(rows, 'r', 25)['association'] == 'changed-around-run'
    assert remote.associate(rows[:3], 'r', 12)['since_run'] == 'unchanged-as-of-latest'
    assert remote.associate(rows, 'r', 40)['association'] == 'observed-before-run-only'
    assert remote.associate(rows, 'r', 5)['association'] == 'observed-after-run-only'
    assert remote.associate(rows[1:2], 'r', 16)['association'] == 'unobserved'
    assert remote.associate(rows, 'other', 12)['association'] == 'unobserved'


def test_bundle_associates_receipts_and_guards_remote_state(tmp_path, server, monkeypatch):
    root = tmp_path / 'p'
    root.mkdir()
    git(root, 'init', '-q')
    git(root, 'config', 'core.autocrlf', 'false')
    (root / 'service.py').write_bytes(b'value=1\n')
    declare(root, ('api', server.route('/api', b'v1')))
    base = commit(root, 'base')
    (root / 'service.py').write_bytes(b'value=2\n')
    head = commit(root, 'patch')
    remote.approve(root, 'api')
    remote.observe(root)
    seed(root)
    remote.observe(root)
    from core.patchproof import report
    value = report.build(root, base, head)
    assert value['binding']['state'] == 'bound'
    section = value['remote_observations']
    association = section['associations'][0]
    assert association['receipt_key'] == value['receipts'][0]['receipt_key']
    assert association['association'] == 'unchanged-around-run'
    assert '## Remote observations' in report.markdown(value)
    original = report.verification_report

    def observe_midway(*args, **kwargs):
        remote.observe(root)
        return original(*args, **kwargs)

    monkeypatch.setattr(report, 'verification_report', observe_midway)
    moved = report.build(root, base, head)
    assert moved['binding']['state'] == 'unavailable'
    assert any('changed during' in issue for issue in moved['binding']['issues'])


def test_unconfigured_projects_keep_their_bundle_and_status(project):
    assert remote.status(project)['state'] == 'not_configured'
    assert remote.markdown(remote.status(project))[2] == 'No remote resources are declared.'


def test_cli_observe_check_and_offline_listing(project, server):
    declare(project, ('ok', server.route('/ok', b'ok')), ('bad', server.route('/bad', status=500)))
    for name in ('ok', 'bad'):
        done = subprocess.run([sys.executable, str(SCRIPT), 'approve-remote', '--project', str(project),
                               '--name', name], capture_output=True, text=True, timeout=60)
        assert done.returncode == 0, done.stderr
    run = [sys.executable, str(SCRIPT), 'observe', '--project', str(project)]
    assert subprocess.run(run, capture_output=True, text=True, timeout=60).returncode == 0
    assert subprocess.run(run + ['--check'], capture_output=True, text=True, timeout=60).returncode == 1
    assert subprocess.run(run + ['--name', 'ok', '--check'], capture_output=True, text=True,
                          timeout=60).returncode == 0
    listing = subprocess.run([sys.executable, str(SCRIPT), 'remotes', '--project', str(project)],
                             capture_output=True, text=True, timeout=60)
    value = json.loads(listing.stdout)
    assert '_rows' not in value and {r['id']: r['state'] for r in value['remotes']} == \
        {'ok': 'observed', 'bad': 'incomplete'}
