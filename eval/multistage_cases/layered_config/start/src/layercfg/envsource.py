"""The environment layer.

The caller passes the environment in as a mapping; nothing here reads
os.environ. `LAYERCFG_SERVER__PORT` sets `server.port`: the prefix is dropped,
the rest is lower-cased and the separator becomes a dot.
"""
from .schema import Entry

ENV_PREFIX = 'LAYERCFG_'
SEPARATOR = '__'


def read_env(env, prefix=ENV_PREFIX):
    """Entries for every variable carrying the prefix, sorted by name."""
    entries = []
    for name in sorted(env):
        if not name.startswith(prefix) or name == prefix:
            continue
        key = name[len(prefix):].lower().replace(SEPARATOR, '.')
        entries.append(Entry(key, env[name], f'env {name}', 'env'))
    return entries
