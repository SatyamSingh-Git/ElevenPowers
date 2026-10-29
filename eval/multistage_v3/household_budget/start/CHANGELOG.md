# Changelog

## Unreleased

- `import --dry-run` shows what a statement would add without storing anything.

## 0.6.0

- `report payees` lists spending per payee over any range of dates.
- `archive` moves a closed year into `archive/<year>.csv`.
- `budget suggest` proposes budgets from the last few months.
- New `app_export` statement layout.

## 0.5.0

- Rollover budgets carry what was left when the previous month was closed.
- `close` writes the month file `closed/<month>.json`.
