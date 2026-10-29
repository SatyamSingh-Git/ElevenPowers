# budgetbook reference

The facts other people and programs rely on. Each table row is
`key | value | meaning`; the meaning says where the fact shows up: the command
line (CLI), a file in the budget folder, or the Python API.

## Budget folder files

| key | value | meaning |
|---|---|---|
| `settings file` | `settings.json` | workspace settings (file) |
| `transactions file` | `transactions.csv` | every transaction (file) |
| `accounts file` | `accounts.json` | accounts and opening balances (file) |
| `rules file` | `rules.json` | categorisation rules, in order (file) |
| `budgets file` | `budgets.json` | monthly budget per category (file) |
| `recurring file` | `recurring.json` | recurring items (file) |
| `goals file` | `goals.json` | savings goals (file) |
| `month file` | `closed/{month}.json` | written by `close`, one per closed month (file) |
| `archive file` | `archive/{year}.csv` | written by `archive`, same columns as the transactions file (file) |

## Settings

| key | value | meaning |
|---|---|---|
| `currency` | `GBP` | default currency code shown in report titles; `init --currency` sets it (settings.json) |
| `report_format` | `text` | format used when a report command is given no `--format` (settings.json) |
| `extra_categories` | `{}` | the household's own categories, name to group (settings.json) |
| `unknown setting` | `unknown setting: {key}` | error for a key settings.json does not know (CLI) |

## Transactions file

| key | value | meaning |
|---|---|---|
| `transactions columns` | `id,date,account,payee,amount,category,memo,source` | header row (transactions file) |
| `transaction date` | `YYYY-MM-DD` | the date column (transactions file) |
| `transaction amount` | `-1234.56` | the amount column: plain decimal, negative is money out (transactions file) |
| `payee column` | `as given, trimmed` | how the payee column is written (transactions file) |
| `uncategorised` | `(empty)` | the category column of an uncategorised transaction (transactions file) |
| `transactions file order` | `by date, then id` | order of the rows (transactions file) |
| `source of add` | `manual` | source column of a transaction recorded with `add` (transactions file) |
| `source of import` | `import:{layout}` | source column of an imported transaction (transactions file) |
| `source of recurring` | `recurring:{name}` | source column of a posted recurring item (transactions file) |
| `ids` | `1, 2, 3, ...` | each new transaction gets the next id after the highest in the file (transactions file) |

## Statement layouts

| key | value | meaning |
|---|---|---|
| `standard` | `Date, Description, Amount` | columns; dates `YYYY-MM-DD`; money out negative (CLI `import --layout`) |
| `debit_credit` | `Date, Description, Debit, Credit` | columns; dates `DD/MM/YYYY`; exactly one of Debit and Credit per row (CLI `import --layout`) |
| `card` | `Transaction Date, Merchant, Amount` | columns; dates `MM/DD/YYYY`; charges positive (CLI `import --layout`) |
| `app_export` | `Type, Started Date, Description, Amount, Fee` | columns; Fee is taken off the amount (CLI `import --layout`) |
| `import --layout` | `recognised from the header` | default when `--layout` is not given (CLI) |
| `duplicate rule` | `same account, date, amount and payee, any case` | a statement row matching a stored transaction is skipped (CLI `import`) |
| `unrecognised layout` | `could not recognise the statement layout; use --layout` | error (CLI `import`) |
| `unknown layout` | `unknown layout: {name}` | error (API `get_layout`) |
| `missing column` | `{layout} statement is missing column: {column}` | error (CLI `import`) |
| `skipped row` | `skipped line {line}: {reason}` | printed on stderr for each row left out (CLI `import`) |

## Rules

| key | value | meaning |
|---|---|---|
| `contains` | `substring, any case` | match kind: the pattern appears in the payee (rules file) |
| `prefix` | `start of the payee, any case` | match kind (rules file) |
| `exact` | `whole payee, any case` | match kind (rules file) |
| `regex` | `regular expression search, any case` | match kind (rules file) |
| `rule order` | `first match wins` | which rule files a payee (rules file) |
| `unknown match kind` | `unknown match kind: {kind}` | error for a rule's `match` (rules file) |

## Searching and registers

| key | value | meaning |
|---|---|---|
| `search --payee` | `text anywhere in the payee, any case` | which transactions `search --payee TEXT` finds (CLI) |
| `search order` | `newest first` | order of `search` results (CLI) |
| `register order` | `by date, then id` | order of `register` lines; the balance runs in that order (CLI) |

## Categories, budgets and spending

| key | value | meaning |
|---|---|---|
| `spending groups` | `essentials, lifestyle, savings` | groups whose money out counts as spending (CLI reports) |
| `income groups` | `income` | groups whose money in counts as income (CLI reports) |
| `ignored groups` | `transfers` | groups left out of income and spending (CLI reports) |
| `uncategorised spending` | `Uncategorised` | name under which uncategorised money out is reported (CLI `report month`) |
| `refunds` | `ignored` | how a positive amount in a spending category counts towards its spent amount (CLI `budget status`) |
| `report category spending` | `same as budget status` | spending per category in the month-end report (CLI `report month`) |
| `budget set --rollover` | `off` | default; with it, a category starts each month with what it had left (CLI) |
| `carried` | `remaining in the previous month file` | what a rollover category starts the month with (CLI `budget status`) |
| `budget status columns` | `Category, Budget, Carried, Spent, Remaining, Used` | (CLI `budget status`) |

## Month file

| key | value | meaning |
|---|---|---|
| `month file fields` | `format, month, currency, income, spending, categories` | top-level fields (month file) |
| `month file category fields` | `name, group, budget, carried, spent, remaining` | fields of each `categories` entry (month file) |
| `month file format` | `1` | the `format` field (month file) |
| `month file amounts` | `integer cents` | how every amount is written (month file) |
| `month file spending` | `as in the month-end report` | `income` and `spending` (month file) |
| `month file spent` | `as in budget status` | each category's `spent` (month file) |

## Reports

| key | value | meaning |
|---|---|---|
| `report formats` | `text, csv, markdown` | values of `--format` (CLI) |
| `text amounts` | `-1,234.56` | amounts in text and markdown output (CLI) |
| `csv amounts` | `-1234.56` | amounts in csv output (CLI) |
| `csv rows` | `section, then the section's columns` | every csv row starts with its section's title; each section has a header row starting `section` (CLI) |
| `month report sections` | `Summary, Spending by category, Top payees` | (CLI `report month`) |
| `top payees` | `5` | payees listed in the month-end report (CLI `report month`) |
| `year report months` | `closed months only` | (CLI `report year`) |

## Recurring items

| key | value | meaning |
|---|---|---|
| `recurring add --every` | `month` | default; `week` is the other choice (CLI) |
| `recurring add --day` | `the start date's day` | default day of the month (CLI) |
| `short months` | `last day of the month` | when a monthly item's day is past the month's end (CLI `recurring post`) |
| `recurring day range` | `day must be between 1 and 31` | error (CLI `recurring add`) |

## Amounts, dates and errors

| key | value | meaning |
|---|---|---|
| `amount decimal places` | `any, truncated` | decimal places accepted in an amount (CLI `add` and statements) |
| `amount thousands separator` | `,` | accepted and ignored in an amount (CLI and statements) |
| `invalid amount` | `invalid amount: {text}` | error (CLI and statements) |
| `invalid date` | `invalid date: {text}` | error (CLI and statements) |
| `invalid month` | `invalid month: {text}` | error (CLI) |
| `unknown account` | `unknown account: {name}` | error (CLI) |
| `unknown category` | `unknown category: {name}` | error (CLI) |
| `account exists` | `account already exists: {name}` | error (CLI `account add`) |
| `account kinds` | `checking, savings, credit` | values of `account add --kind`; default `checking` (CLI) |
| `zero amount` | `amount must not be zero` | error (CLI `add`) |
| `month is closed` | `month is closed: {month}` | error for a change in a closed month (CLI) |
| `month already closed` | `month already closed: {month}` | error (CLI `close`) |
| `negative budget` | `budget must not be negative: {amount}` | error (CLI `budget set`) |
| `error output` | `error: {message}` | printed on stderr; exit status 1 (CLI) |
