# ledgerbook reference

Amounts inside the library are integers of minor units (cents for USD). Each
table lists one documented fact per row: its key, its value, and what it means.

## Amounts

| Key | Value | Meaning |
| --- | --- | --- |
| `default_currency` | `USD` | Currency of a `Ledger()` or `init` without one |
| `amount.unit` | `integer minor units` | What every amount passed to or returned by the library counts |
| `amount.input` | `-?digits[.digits]` | Decimal text `parse_amount` accepts; no `+`, no separators |
| `amount.grouping` | `none` | Separator `format_amount` puts between groups of thousands |
| `error.bad_amount` | `invalid amount: {text}` | `AmountError` for text that is not a decimal number |
| `error.too_precise` | `too many decimal places for {currency}: {text}` | `AmountError` when the text has more decimals than the currency |
| `error.unknown_currency` | `unknown currency: {currency}` | `AmountError` for a code missing from the ISO 4217 table |

## Accounts

| Key | Value | Meaning |
| --- | --- | --- |
| `account.separator` | `:` | Joins the segments of an account name |
| `account.roots` | `Assets, Liabilities, Equity, Income, Expenses` | Allowed first segments; the root fixes the account type |
| `account.debit_normal` | `asset, expense` | Types that grow with debits; the others grow with credits |
| `error.bad_account` | `invalid account name: {name}` | `AccountError` for a malformed name or unknown root |
| `error.duplicate_account` | `account already open: {name}` | `AccountError` when opening an account twice |
| `error.unknown_account` | `unknown account: {name}` | `AccountError` for an account that was never opened |

## Transactions

| Key | Value | Meaning |
| --- | --- | --- |
| `transaction.date` | `YYYY-MM-DD string` | Type of `Transaction.date` and of `StatementLine.date` |
| `posting.sign` | `debit positive, credit negative` | Sign of a posting amount |
| `limit.min_postings` | `2` | Fewest postings in one transaction |
| `limit.max_postings` | `16` | Most postings in one transaction |
| `limit.description_length` | `120` | Longest description, in characters |
| `error.bad_date` | `invalid date: {value}` | `LedgerError` for a date that is not a real YYYY-MM-DD date |
| `error.description` | `description must be 1 to 120 characters` | `LedgerError` for an empty or overlong description |
| `error.too_few_postings` | `transaction needs at least 2 postings` | `LedgerError` |
| `error.too_many_postings` | `transaction has more than 16 postings` | `LedgerError` |
| `error.posting_type` | `posting amount must be an integer: {amount!r}` | `LedgerError` for a float, bool or text amount |
| `error.unbalanced` | `transaction does not balance: off by {difference}` | `UnbalancedError`; the difference is in minor units |
| `reversal.description` | `Reversal: {description}` | Default description of `reversal()`, cut to 120 characters |

## Balances and reports

| Key | Value | Meaning |
| --- | --- | --- |
| `balance.sign` | `debit positive` | Sign of `Ledger.balance`, `balances`, `subtotal` and statement balances |
| `trial_balance.columns` | `Account, Debit, Credit` | Columns of the rendered trial balance |
| `trial_balance.total_label` | `Total` | Label of its last row |
| `statement.columns` | `Date, Description, Amount, Balance` | Columns of a rendered statement |
| `summary.keys` | `assets, liabilities, equity, income, expenses, net_income` | Keys of `summary()`; each is positive for a normal balance |

## Journal file

| Key | Value | Meaning |
| --- | --- | --- |
| `journal.encoding` | `UTF-8, one JSON object per line` | Blank lines are skipped |
| `journal.version` | `1` | Version written in the header |
| `journal.header` | `{"ledgerbook": <version>, "currency": <code>}` | First line of every journal |
| `record.open` | `{"type": "open", "account": <name>}` | Opens an account |
| `record.txn` | `{"type": "txn", "date", "description", "postings"}` | A transaction; `date` is YYYY-MM-DD |
| `record.posting` | `{"account": <name>, "amount": <amount>}` | One element of `postings` |
| `record.posting.amount` | `integer minor units` | How a posting amount is written |
| `error.journal` | `line {line}: {problem}` | `JournalError`; any `LedgerError` while replaying is wrapped this way |
| `error.journal_version` | `unsupported journal version: {version}` | Header with a version this release cannot read |
| `error.missing_header` | `missing header` | Problem reported for an empty journal |
| `error.missing_field` | `missing field: {name}` | Problem reported for a record without a required field |
| `error.journal_exists` | `journal already exists: {path}` | `LedgerError` from `JournalWriter.create` and `init` |

## Command line

| Key | Value | Meaning |
| --- | --- | --- |
| `cli.usage` | `ledgerbook JOURNAL COMMAND` | Every command names its journal first |
| `cli.commands` | `init, open, post, reverse, balances, summary, statement` | Available commands |
| `cli.posting` | `ACCOUNT=AMOUNT` | Posting argument; one may be a bare `ACCOUNT` that takes the remainder |
| `cli.exit_ok` | `0` | Exit status on success |
| `cli.exit_error` | `1` | Exit status after printing `error: <message>` to stderr |
| `error.remainder` | `only one posting may omit its amount` | More than one bare `ACCOUNT` in `post` |
| `error.no_transaction` | `no transaction number {number}` | `reverse` with a number outside the journal |
