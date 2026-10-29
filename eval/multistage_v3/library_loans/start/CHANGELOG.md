# Changelog

## Unreleased

## 1.4.0 - 2026-02-20

- Copies returned at another branch go into transit; `lend receive` takes them off the van.
- Staff notes on member accounts (`lend note`, `lend notes`, `lend clear-notes`).
- `lend amnesty` waives fines charged before a date.
- `lend lateness` and `lend lapsed` reports.

## 1.3.0 - 2025-11-03

- Courtesy reminders before the due date (`courtesy_days`).
- Stocktake against scanner files (`lend stocktake`).
- Zip backups (`lend backup`, `lend restore`).

## 1.2.0 - 2025-07-14

- Members owing `block_at` or more cannot borrow.
- Lost copies can be written off and charged (`lend lost`).
- Fine waivers (`lend waive`) and the `lend takings` report for finance.
