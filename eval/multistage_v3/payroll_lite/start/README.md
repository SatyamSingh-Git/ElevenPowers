# payroll

Payroll for a small business, run from the command line. Supervisors send in
timesheets as CSV; payroll works out overtime, allowances, deductions and tax,
saves each pay run, and prints payslips, the bank's payment file and the
year-end summary.

```
payroll --data ./books timesheet import week2.csv --period 2026-W02
payroll --data ./books check --period 2026-W02
payroll --data ./books run --period 2026-W02
payroll --data ./books payslip --period 2026-W02 --employee E001
payroll --data ./books bank-file --period 2026-W02
payroll --data ./books year-end --year 2026 --format csv
```

Everything payroll knows lives in the data directory: `payroll.ini`,
`employees.json`, `timesheets/`, `runs/` and `bank/`. See
[docs/reference.md](docs/reference.md) for every setting, file format and
message.

Public holidays and tax bands come from `src/payroll/_generated.py`, which is
generated from the finance team's sheet.

Standard library only; Python 3.11 or later. Run the tests with
`PYTHONPATH=src python -m pytest`.
