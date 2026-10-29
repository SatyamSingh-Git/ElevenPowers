# Changelog

## Unreleased

## 1.4.0 - 2026-04-02

- Add `schedule`, which turns the irrigation plan into the valve controller's schedule.
- Add `water`, the litres the current suggestions would use, from each zone's `flow_lpm`.
- `ingest` accepts several files at once and totals the counts.

## 1.3.0 - 2026-02-16

- Add `condensation`, `gdd` and `trend` views.
- Add `archive`, which moves readings older than `archive_after_days` into monthly files.
- `check --dry-run` prints new alerts without logging them.

## 1.2.0 - 2025-12-01

- Add the daily light integral and photoperiod to `report` and the new `light` view.
- Add vapour pressure deficit and dew point (`climate`).
- Reject duplicate rows within one controller export.
