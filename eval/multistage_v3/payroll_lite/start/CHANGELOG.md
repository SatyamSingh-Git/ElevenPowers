# Changelog

## Unreleased

- `payroll journal` prints the ledger entry for a pay run, as text or CSV.
- `payroll compare` defaults to the period before when `--against` is left out.

## 1.4.0

- `payroll reconcile` checks the bank's statement against the payment file for a period.
- Payslips end with year-to-date totals.
- `payroll leave` keeps annual leave balances built up from each pay run.

## 1.3.0

- `payroll year-end --format csv` for the accountant.
- `payroll timesheet blank` writes a sheet for supervisors to fill in; rows left without hours are skipped on import.
