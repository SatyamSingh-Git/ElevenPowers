"""Read-only presentation of saved strength; never executes a test or engine."""
from . import store
from .isolation import copy_plan, fingerprint
from .reuse import execution_stamp
from .settings import settings


def view(root, task, config, source_fingerprint, deadline):
    saved = store.load(root, task)
    if saved is None:
        return {'state': 'not_recorded', 'freshness': 'unknown', 'issues': [],
                'observations': [], 'summary': {}, 'limitations': []}
    keys = ('state', 'baseline', 'attempts', 'recorded_at', 'paths', 'engine_versions',
            'observations', 'summary', 'command', 'limitations')
    value = {key: saved[key] for key in keys if key in saved}
    value['issues'] = list(saved.get('issues', []))
    value['freshness'] = 'unknown'
    if saved.get('state') == 'running':
        value['issues'].append('execution is running or was interrupted before a final observation')
    if not saved.get('fingerprint'):
        return value
    try:
        options = settings(saved['settings'])
        paths = copy_plan(root, options, deadline)
        current = execution_stamp(fingerprint(root, paths, options, deadline))
        value['freshness'] = 'fresh' if (current == saved['fingerprint'] and
            source_fingerprint == saved['source_fingerprint']) else 'stale'
        current_command = config.strength.get('command') or config.command_for('tests')
        if current_command != saved['command']:
            value['freshness'] = 'stale'
            value['issues'].append('current declared/focused command differs from this saved observation')
    except (OSError, ValueError, TimeoutError):
        value['issues'].append('saved test-strength input freshness could not be checked within the report limits')
    return value
