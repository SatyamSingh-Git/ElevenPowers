# throttle reference

## Policies

| Fact | Value | Meaning |
|---|---|---|
| `policy.syntax` | `<limit>/<period>[; name=value]...` | How a policy is written, e.g. `100/minute; algorithm=sliding`. |
| `policy.period_units` | `ms, s, sec, second, m, min, minute, h, hour, d, day` | Units a period may use; a unit alone means one of it. |
| `policy.bare_period` | `seconds` | Unit of a period written as a bare number (`10/30`). |
| `policy.algorithms` | `fixed, sliding, bucket` | Values of the `algorithm` option. |
| `policy.algorithm.default` | `fixed` | Algorithm when the option is left out. |
| `policy.burst.default` | `limit` | Bucket capacity when `burst` is left out. Only buckets take `burst`. |

## Throttle

| Fact | Value | Meaning |
|---|---|---|
| `throttle.default_policy` | `60/minute` | Policy for keys that match no pattern. |
| `throttle.max_keys` | `1000` | Keys tracked at once before eviction. |
| `throttle.eviction` | `least recently used key` | Which key is forgotten when `max_keys` is reached. |
| `throttle.pattern` | `exact key, or prefix ending in *; longest pattern wins` | How `set_policy` patterns match keys. |
| `clock.read` | `clock.now()` | How limiters read the current time, in seconds, from the clock they are given. |
| `bucket.signature` | `TokenBucket(capacity, refill_per_second, clock)` | Constructing a token bucket directly. |

## Decision

Returned by `hit()` on a limiter or a Throttle.

| Fact | Value | Meaning |
|---|---|---|
| `decision.allowed` | `bool` | Whether the hit was let through. |
| `decision.remaining` | `int, units left after this hit` | |
| `decision.retry_after` | `seconds` | How long until the same hit would be allowed: a float, 0 when allowed. |
| `decision.limit` | `int` | The limiter's limit (a bucket's capacity). |

## Limiter state and snapshots

`state()` on a limiter returns a dict; `Throttle.snapshot()` returns one such
dict per key, sorted by key, with `key`, `policy` and `retry_after` added.

| Fact | Value | Meaning |
|---|---|---|
| `state.kind` | `fixed, sliding or bucket` | Which algorithm. |
| `state.limit` | `int` | Limit, or a bucket's capacity. |
| `state.remaining` | `int` | Units available now. |
| `state.reset_in` | `float seconds until full again` | 0 when nothing is spent. |
| `snapshot.key` | `str` | The key. |
| `snapshot.policy` | `policy text` | The key's policy, written as `parse_policy` reads it. |
| `snapshot.retry_after` | `same unit as decision.retry_after` | What a hit of 1 would be told now. |

## Reports

| Fact | Value | Meaning |
|---|---|---|
| `report.columns` | `key, policy, remaining, retry, resets` | Columns of `render_table`; remaining is shown as `left/limit`. |
| `report.empty_wait` | `-` | Shown in `retry` and `resets` when there is nothing to wait for. |
| `report.csv` | `one row per snapshot entry, columns in snapshot order` | Output of `to_csv()`; empty when no keys are tracked. |
| `duration.format` | `250ms below 1s, 1.5s below 1m, then 1h2m3s` | How waits are written in reports and messages. |

`summarise()` returns `keys`, `exhausted` and `busiest`.

## Config files

| Fact | Value | Meaning |
|---|---|---|
| `config.comment` | `#` | Starts a comment, anywhere on a line. |
| `config.settings` | `default, max_keys, limit <pattern>` | Settings a config line may set. |

## Errors

| Fact | Value | Meaning |
|---|---|---|
| `error.invalid_policy` | `invalid policy: {text}` | PolicyError. |
| `error.invalid_option` | `invalid option: {text}` | PolicyError: an option without `=`. |
| `error.unknown_option` | `unknown option: {name}` | PolicyError. |
| `error.unknown_algorithm` | `unknown algorithm: {name}` | PolicyError. |
| `error.burst` | `burst must be a positive integer: {value}` | PolicyError. |
| `error.burst_algorithm` | `burst only applies to the bucket algorithm` | PolicyError. |
| `error.invalid_duration` | `invalid duration: {text}` | ValueError; PolicyError inside a policy. |
| `error.unknown_unit` | `unknown unit: {unit}` | ValueError; PolicyError inside a policy. |
| `error.limit` | `limit must be positive: {limit}` | ValueError. |
| `error.period` | `period must be positive: {value}` | ValueError. |
| `error.refill` | `refill_per_second must be positive: {value}` | ValueError from TokenBucket. |
| `error.cost` | `cost must be at least 1: {cost}` | ValueError from `hit()`. |
| `error.max_keys` | `max_keys must be at least 1: {value}` | ValueError from Throttle. |
| `error.rate_limited` | `rate limit exceeded for {key}: retry in {wait}` | RateLimitExceeded from `check()`; `{wait}` as in `duration.format`. |
| `error.config` | `config line {n}: {problem}` | ConfigError; `{problem}` may be any policy error. |
| `error.config_syntax` | `expected name = value` | ConfigError problem. |
| `error.config_setting` | `unknown setting: {name}` | ConfigError problem. |
| `error.config_max_keys` | `max_keys must be an integer: {value}` | ConfigError problem. |
| `error.clock` | `clock cannot go backwards` | ValueError from ManualClock. |
