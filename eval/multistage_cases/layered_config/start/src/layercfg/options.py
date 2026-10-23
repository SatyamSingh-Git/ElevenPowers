"""The options the application understands."""
from .schema import Option, Schema

APP_SCHEMA = Schema([
    Option('server.host', 'str', '127.0.0.1', 'Address to listen on.', aliases=('server.bind',)),
    Option('server.port', 'int', '8080', 'TCP port to listen on.', aliases=('server.listen_port',),
           minimum='1', maximum='65535'),
    Option('server.timeout', 'duration', '30s', 'How long one request may take.', minimum='1s', maximum='10m'),
    Option('server.allowed_hosts', 'list', 'localhost', 'Host header values that are served.'),
    Option('server.tls_cert', 'str', None, 'Path to the TLS certificate.'),
    Option('server.tls_key', 'str', None, 'Path to the TLS private key.'),
    Option('pool.min_size', 'int', '1', 'Connections kept open when idle.', minimum='0', maximum='1000'),
    Option('pool.max_size', 'int', '10', 'Most connections open at once.', minimum='1', maximum='1000'),
    Option('pool.idle_timeout', 'duration', '5m', 'Idle connections are closed after this long.',
           minimum='0s', maximum='1d'),
    Option('cache.max_bytes', 'size', '64mb', 'Memory the response cache may use.', minimum='0b', maximum='4gb'),
    Option('cache.evict_ratio', 'float', '0.75', 'Share of the cache kept when it is full.',
           minimum='0', maximum='1'),
    Option('log.level', 'choice', 'info', 'Least severe message that is logged.', aliases=('log.verbosity',),
           choices=('debug', 'info', 'warning', 'error')),
    Option('log.file', 'str', None, 'Log to this file instead of standard error.'),
    Option('app.name', 'str', 'layercfg-app', 'Name shown in logs and the status page.'),
    Option('app.debug', 'bool', 'false', 'Turn on debug pages.', aliases=('app.dev_mode',)),
    Option('db.url', 'str', 'sqlite:///app.db', 'Database connection URL.'),
    Option('db.password', 'str', None, 'Database password.', secret=True),
])
