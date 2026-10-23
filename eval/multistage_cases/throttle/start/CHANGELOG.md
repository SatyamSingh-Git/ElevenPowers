# Changelog

## Unreleased

## 0.4.0

- Config files: `dump_config()` writes a Throttle's policies back out.
- `Throttle.remove_policy()` and `Throttle.policies()`.
- `nearest_limit()` lists the keys closest to their limits.

## 0.3.0

- Sliding window limiter (`algorithm=sliding`).
- `to_csv()` exports a snapshot.
