# layercfg reference

The facts callers and operators rely on. The second column of every table is
exact.

## Options

| Option | Default | Meaning |
|---|---|---|
| `server.host` | `127.0.0.1` | str. Address to listen on. |
| `server.port` | `8080` | int. TCP port to listen on. |
| `server.timeout` | `30s` | duration. How long one request may take. |
| `server.allowed_hosts` | `localhost` | list. Host header values that are served. |
| `server.tls_cert` | `(unset)` | str. Path to the TLS certificate. |
| `server.tls_key` | `(unset)` | str. Path to the TLS private key. |
| `pool.min_size` | `1` | int. Connections kept open when idle. |
| `pool.max_size` | `10` | int. Most connections open at once. |
| `pool.idle_timeout` | `5m` | duration. Idle connections are closed after this long. |
| `cache.max_bytes` | `64mb` | size. Memory the response cache may use. |
| `cache.evict_ratio` | `0.75` | float. Share of the cache kept when it is full. |
| `log.level` | `info` | choice of `debug`, `info`, `warning`, `error`. |
| `log.file` | `(unset)` | str. Log to this file instead of standard error. |
| `app.name` | `layercfg-app` | str. Name shown in logs and the status page. |
| `app.debug` | `false` | bool. Turn on debug pages. |
| `db.url` | `sqlite:///app.db` | str. Database connection URL. |
| `db.password` | `(unset)` | str, secret. Database password. |

## Ranges

Inclusive, written in the option's own unit.

| Option | Range | Notes |
|---|---|---|
| `range.server.port` | `1..65535` | |
| `range.server.timeout` | `1s..10m` | |
| `range.pool.min_size` | `0..1000` | |
| `range.pool.max_size` | `1..1000` | |
| `range.pool.idle_timeout` | `0s..1d` | |
| `range.cache.max_bytes` | `0b..4gb` | |
| `range.cache.evict_ratio` | `0..1` | |

## Aliases

An alias is accepted anywhere the option's key is: in the file, in the
environment and when reading a value.

| Alias | Option | Notes |
|---|---|---|
| `server.bind` | `server.host` | |
| `server.listen_port` | `server.port` | |
| `log.verbosity` | `log.level` | |
| `app.dev_mode` | `app.debug` | |

## Types

Surrounding spaces are removed from every raw value before it is read.

| Type | Value | Notes |
|---|---|---|
| `int` | `decimal integer` | |
| `float` | `finite decimal number` | |
| `bool` | `true/false, yes/no, on/off, 1/0` | |
| `str` | `text as written` | |
| `duration` | `float seconds` | A number with an optional unit, such as `1.5s`. |
| `duration.units` | `ms s m h d` | |
| `duration.bare` | `seconds` | Unit of a duration written without one. |
| `size` | `int bytes` | A whole number with an optional unit; units are powers of 1024. |
| `size.units` | `b kb mb gb tb` | |
| `list` | `comma-separated` | Empty items are dropped. |
| `choice` | `exact match` | |

## Layers and sources

| Fact | Value | Notes |
|---|---|---|
| `layers` | `defaults < file < env` | A later layer overrides an earlier one. |
| `source.default` | `default` | What `Config.source` returns for a built-in default. |
| `source.file` | `{file} line {line}` | |
| `source.env` | `env {name}` | |

## Environment

The environment is passed in as a mapping; `os.environ` is never read by the
library.

| Fact | Value | Notes |
|---|---|---|
| `env.prefix` | `LAYERCFG_` | Variables without it are ignored. |
| `env.separator` | `__` | Stands for the dot between section and name. |
| `env.example` | `LAYERCFG_SERVER__PORT` | Sets `server.port`. |
| `env.unknown` | `error` | A prefixed variable that names no option is reported. |

## File format

| Fact | Value | Notes |
|---|---|---|
| `file.encoding` | `utf-8` | A leading byte order mark is ignored. |
| `file.comment` | `# ;` | Only at the start of a line. |
| `file.continuation` | `indented line` | Joined to the value above with one space. |
| `file.duplicate` | `last wins` | |

## Messages

Each problem is reported as one line, `{source}: {message}`. All problems in all
layers are reported together; a syntax error in the file stops loading.

| Message | Text | Notes |
|---|---|---|
| `msg.issue` | `{source}: {message}` | |
| `msg.type` | `{key}: expected {type}, got '{raw}'` | |
| `msg.min` | `{key}: must be at least {min}` | |
| `msg.max` | `{key}: must be at most {max}` | |
| `msg.choice` | `{key}: must be one of {choices}` | Choices joined with `, `. |
| `msg.unknown_key` | `unknown key '{key}'` | A file key that names no option. |
| `msg.unknown_env` | `unknown variable` | |
| `msg.syntax` | `expected 'key = value' or '[section]'` | |
| `msg.no_section` | `key outside of a section` | |
| `msg.bad_section` | `bad section name '{name}'` | |
| `msg.lookup` | `unknown key '{key}'` | `get` and `explain` on the command line. |
| `msg.unreadable` | `cannot read {path}: {reason}` | |

## Views and command line

| Fact | Value | Notes |
|---|---|---|
| `dump.formats` | `ini json sources` | `ini` loads back to the same values. |
| `dump.mask` | `***` | Shown instead of a secret unless `--reveal` is given. |
| `dump.unset` | `; {name} =` | An unset option in the `ini` view. |
| `cli.commands` | `get dump check explain keys version` | |
| `cli.config` | `--config PATH` | |
| `exit.ok` | `0` | |
| `exit.invalid` | `1` | The configuration has problems. |
| `exit.usage` | `2` | Unknown key, unreadable file or bad arguments. |
| `version` | `1.4.0` | |
