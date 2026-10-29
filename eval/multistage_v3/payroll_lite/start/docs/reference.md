# Payroll reference

Every documented behaviour, one row each. The first cell is the name of the fact,
the second its value, and the last says where it shows: the command line, the
`payroll.ini` file, a file payroll writes or reads, or the pay rules themselves.

## Settings

All settings live in `payroll.ini` in the data directory. A missing file or key
uses the default below.

| setting | default | meaning |
|---|---|---|
| `company.name` | `Example Co` | `payroll.ini` file: company name printed on payslips and statements |
| `company.pay_frequency` | `weekly` | `payroll.ini` file: `weekly`, `fortnightly` or `monthly` |
| `company.first_period_start` | `2026-01-05` | `payroll.ini` file: start date of the first pay period |
| `company.pay_delay_days` | `3` | `payroll.ini` file: days from the end of a period to its pay date |
| `overtime.daily_threshold` | `8` | `payroll.ini` file: hours in one day paid at the ordinary rate before overtime starts |
| `overtime.multiplier` | `1.5` | `payroll.ini` file: overtime rate as a multiple of the hourly rate |
| `overtime.holiday_multiplier` | `2.0` | `payroll.ini` file: rate for work on a public holiday, as a multiple of the hourly rate |
| `timesheet.max_hours_per_day` | `24` | `payroll.ini` file: most hours one timesheet row may hold |
| `error.unknown_setting` | `unknown setting {section}.{key}` | command line: a key `payroll.ini` does not know |
| `error.bad_setting` | `bad setting {section}.{key}: {value}` | command line: a value that cannot be used |

## Pay rules

Weekly pay has `52` periods a year, fortnightly `26` and monthly `12`. Hourly
staff are paid for the hours in the stored timesheet; hourly staff with no hours
in a period get no payslip. Salaried staff are paid their yearly salary divided
by the periods in a year, whatever their timesheet says.

A day's work on a public holiday is all paid at the holiday rate and is never
ordinary or overtime. On other days, work beyond `overtime.daily_threshold`
hours is overtime. Sick hours are paid at the ordinary rate and never count as
overtime.

Gross pay is wages plus the allowances counted in gross. Tax is worked out on
gross pay. Deductions come off after tax. Net pay is gross pay less tax and
deductions.

| rule | value | meaning |
|---|---|---|
| `periods_per_year.weekly` | `52` | pay rules: periods in a year for weekly pay |
| `periods_per_year.fortnightly` | `26` | pay rules: periods in a year for fortnightly pay |
| `periods_per_year.monthly` | `12` | pay rules: periods in a year for monthly pay |
| `money.rounding` | `half-up to the cent` | pay rules: every amount, each line rounded on its own |
| `employee.pay_types` | `hourly, salaried` | pay rules: the pay types an employee can have |
| `allowance.kinds` | `fixed, per_shift` | pay rules: `fixed` is paid each period, `per_shift` for each day with work |
| `allowance.taxable_kinds` | `fixed, per_shift` | pay rules: allowance kinds counted in gross pay, and so taxed |
| `deduction.kinds` | `fixed, percent` | pay rules: `fixed` takes `amount`, `percent` takes `rate` percent of gross pay |
| `tax.method` | `annualised bands` | pay rules: the period's gross times the periods in a year, taxed on the yearly bands, divided back |

## Files in the data directory

### `employees.json`

```json
{"employees": [{"id": "E001", "name": "Ana Lima", "pay_type": "hourly", "rate": "25.00",
  "bank_account": "11-1111-0000001-00", "active": true, "department": "General",
  "allowances": [{"kind": "per_shift", "label": "Meal", "amount": "8.00"}],
  "deductions": [{"kind": "percent", "label": "Pension", "rate": "5"}]}]}
```

`active` and `department` may be left out; they default to `true` and `General`.

| field | value | meaning |
|---|---|---|
| `employees.path` | `employees.json` | employees file: where it lives in the data directory |
| `employees.fields` | `id, name, pay_type, rate, bank_account, active, department, allowances, deductions` | employees file: fields of each employee |
| `employees.id_format` | `capital letter, then 1 to 9 capitals or digits` | employees file: what an employee id looks like |
| `employees.bank_account_format` | `NN-NNNN-NNNNNNN-NN` | employees file: what a bank account looks like |
| `employees.rate` | `hourly rate or yearly salary` | employees file: meaning of `rate` by pay type |

### Uploaded timesheets

A supervisor's timesheet is a CSV with a header row. Rows with no hours are
skipped, so the sheet from `payroll timesheet blank` can be imported as it is
filled in. An import is all or nothing: if any row is bad, every bad row is
reported and nothing is stored.

| field | value | meaning |
|---|---|---|
| `timesheet.columns` | `employee_id, date, hours, kind` | uploaded timesheet file: columns; `kind` may be left out |
| `timesheet.kinds` | `work, sick` | uploaded timesheet file: kinds of hours |
| `timesheet.kind_default` | `work` | uploaded timesheet file: kind of a row whose `kind` is empty |
| `timesheet.date_format` | `YYYY-MM-DD` | uploaded timesheet file: how dates are written |
| `timesheet.error.line` | `line {line}: {problem}` | command line: each rejected row, by its line in the file |
| `timesheet.error.missing_column` | `missing column {column}` | command line: the file lacks a column |
| `timesheet.error.employee` | `unknown employee {employee}` | command line: a row for someone not on the payroll |
| `timesheet.error.date` | `bad date {value}` | command line: a date that cannot be read |
| `timesheet.error.outside` | `{date} is outside period {period}` | command line: a date in another period |
| `timesheet.error.hours` | `hours must be more than 0 and at most {max}` | command line: hours that are not a number or out of range |
| `timesheet.error.kind` | `unknown kind {kind}` | command line: a kind that is not `work` or `sick` |
| `timesheet.error.duplicate` | `duplicate row for {employee} on {date}` | command line: the same employee, day and kind twice |

### Stored timesheets

| field | value | meaning |
|---|---|---|
| `timesheet.stored_path` | `timesheets/{period}.csv` | stored timesheet file: where the accepted hours for a period are kept |
| `timesheet.stored_columns` | `employee_id, date, hours, kind` | stored timesheet file: columns, with a header row |
| `timesheet.row_order` | `employee_id, date, kind` | stored timesheet file: order of the rows, which `payroll timesheet show` prints as stored |

### Pay-run files

`payroll run` saves each pay run as JSON. Payslips, bank files, statements and
the year-end summary are all made from these files.

| field | value | meaning |
|---|---|---|
| `payrun.path` | `runs/{period}.json` | pay-run file: where a period's pay run is saved |
| `payrun.schema` | `1` | pay-run file: value of `schema` |
| `payrun.money` | `decimal string` | pay-run file: how money amounts are written, for example `"1012.50"` |
| `payrun.hours` | `decimal string` | pay-run file: how line hours are written, for example `"39.00"` |
| `payrun.fields` | `schema, period, start, end, pay_date, payslips, totals` | pay-run file: top-level fields |
| `payrun.payslip_fields` | `employee_id, name, gross, tax, deductions, net, lines` | pay-run file: fields of each payslip |
| `payrun.line_fields` | `kind, label, hours, rate, amount` | pay-run file: fields of each payslip line; `hours` and `rate` may be null |
| `payrun.totals_fields` | `gross, tax, deductions, net` | pay-run file: fields of `totals` |

Line kinds are `basic`, `overtime`, `holiday`, `sick`, `allowance` and
`deduction`.

### Bank files

| field | value | meaning |
|---|---|---|
| `bank.path` | `bank/{period}.csv` | bank file: default place `payroll bank-file` writes to |
| `bank.columns` | `account, name, amount, reference` | bank file: columns of each row |
| `bank.header` | `none` | bank file: the bank's format has no header row |
| `bank.reference` | `PAY {period}` | bank file: payment reference |
| `bank.name_length` | `20` | bank file: names are cut to this many characters |
| `bank.error.duplicate` | `two payments to account {account}; check the bank details of {name}` | command line: one account paid twice |

### Bank statements

| field | value | meaning |
|---|---|---|
| `statement.columns` | `date, account, reference, amount` | bank statement file: columns read by `payroll reconcile`, with a header row |
| `statement.error.column` | `statement is missing column {column}` | command line: the statement lacks a column |

## Command line

Every command takes `--data DIR`. Errors are printed to standard error as
`error: {message}`.

| item | value | meaning |
|---|---|---|
| `--data` | `.` | command line: data directory |
| `exit.ok` | `0` | command line: exit status on success |
| `exit.error` | `1` | command line: exit status after an error |
| `exit.usage` | `2` | command line: exit status for a mistyped command |
| `error.prefix` | `error: {message}` | command line: how errors are printed |
| `error.period` | `not a period id: {period}` | command line: a period id the calendar does not have |
| `error.unknown_employee` | `unknown employee {employee}` | command line: an employee id that is not on the payroll |
| `error.run_exists` | `pay run {period} already exists; use --replace` | command line: `payroll run` for a period already paid |
| `error.no_run` | `no pay run for {period}` | command line: a command that needs a pay run that does not exist |
| `error.no_payslip` | `no payslip for {employee} in {period}` | command line: `payroll payslip` for someone not paid that period |
| `run --replace` | `off` | command line: `payroll run` refuses to overwrite a pay run unless given |
| `payslip.gross_label` | `Gross pay` | command line: `payroll payslip` line with gross pay |
| `payslip.tax_label` | `Tax` | command line: `payroll payslip` line with tax |
| `payslip.net_label` | `Net pay` | command line: `payroll payslip` line with net pay |
| `payslip.year_to_date` | `Year to date: gross {gross}, tax {tax}, deductions {deductions}, net {net}` | command line: last line of `payroll payslip` |
| `hours.columns` | `employee, ordinary, overtime, holiday, sick, total` | command line: columns of `payroll hours`; each shows the hours the pay run pays that way |
| `hours.decimals` | `1` | command line: decimal places of hours in `payroll hours` |
| `year-end.columns` | `employee_id, name, gross, tax, deductions, net` | command line: columns of `payroll year-end`, in both formats |
| `year-end.formats` | `text, csv` | command line: values of `payroll year-end --format` |
| `year-end --format` | `text` | command line: default format of `payroll year-end` |
| `year-end.counts_by` | `pay date` | command line: `payroll year-end` counts a pay run in the year it is paid |
| `journal.columns` | `account, debit, credit` | command line: columns of `payroll journal`; debits and credits always balance |
| `journal --format` | `text` | command line: default format of `payroll journal` |
| `reconcile.line` | `{account} {name}: {status}` | command line: each line `payroll reconcile` prints |
| `reconcile.matched` | `matched` | command line: payment found with the right amount |
| `reconcile.missing` | `missing` | command line: payment not on the statement |
| `reconcile.wrong_amount` | `wrong amount: paid {paid}, expected {expected}` | command line: payment found with another amount |
| `reconcile.unexpected` | `unexpected` | command line: statement line with our reference that matches no payment |
| `reconcile.exit` | `1` | command line: exit status of `payroll reconcile` when anything is not matched |
| `check.long_day` | `12` | command line: `payroll check` warns about days with more hours than this |
| `compare.flag_share` | `0.20` | command line: `payroll compare` flags a net pay change bigger than this share |
| `leave.hourly_share` | `4/52` | command line: `payroll leave accrue` hours earned per ordinary hour paid |
| `leave.salaried_hours_per_year` | `160` | command line: `payroll leave accrue` hours a salaried employee earns in a year |
| `leave.path` | `leave.json` | leave file: where leave balances are kept |
