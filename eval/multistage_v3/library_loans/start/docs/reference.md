# lending reference

The facts the desk, finance and scripts rely on. Each table row is
`key | value | meaning`.

## Library directory

A library is one directory. `lend --library DIR` points at it.

| key | value | meaning |
|---|---|---|
| `files.catalogue` | `catalogue.json` | titles and their copies (file) |
| `files.members` | `members.json` | registered members (file) |
| `files.holds` | `holds.json` | open holds, in queue order (file) |
| `files.ledger` | `loans.ledger` | the loans ledger, every circulation event and payment (file) |
| `files.settings` | `lending.ini` | branch settings; optional (file) |
| `files.holidays` | `holidays.txt` | dates the library is closed, one per line; optional (file) |
| `files.outbox` | `outbox.jsonl` | notices waiting for the mail run (file) |
| `files.transit` | `transit.json` | copies travelling back to their home branch (file) |
| `files.notes` | `notes.json` | staff notes on member accounts (file) |

## Settings

Options go in the `[lending]` section of `lending.ini`. Money is written in
pounds. Per-material options carry the material code after a dot.

| key | value | meaning |
|---|---|---|
| `loan_days.BK` | `21` | loan period for books, in days (lending.ini option) |
| `loan_days.AB` | `14` | loan period for audiobooks, in days (lending.ini option) |
| `loan_days.DVD` | `7` | loan period for DVDs, in days (lending.ini option) |
| `loan_days.MAG` | `7` | loan period for magazines, in days (lending.ini option) |
| `fine_per_day.BK` | `0.25` | fine per day late for books (lending.ini option) |
| `fine_per_day.AB` | `0.25` | fine per day late for audiobooks (lending.ini option) |
| `fine_per_day.DVD` | `1.00` | fine per day late for DVDs (lending.ini option) |
| `fine_per_day.MAG` | `0.10` | fine per day late for magazines (lending.ini option) |
| `max_fine` | `10.00` | most one late return can be fined; never more than the copy's price either (lending.ini option) |
| `block_at` | `5.00` | a member owing this much or more cannot borrow (lending.ini option) |
| `max_renewals` | `2` | renewals allowed per loan (lending.ini option) |
| `max_holds` | `10` | holds one member may have open at once (lending.ini option) |
| `hold_pickup_days` | `7` | days a member has to collect a copy set aside for them (lending.ini option) |
| `notice_days` | `7,21` | days past the due date on which overdue reminders go out (lending.ini option) |
| `courtesy_days` | `2` | days before the due date a courtesy reminder goes out; 0 turns it off (lending.ini option) |
| `closed_days` | `(none)` | weekdays the library is closed, such as `sun`; a due date falling on one moves to the next open day (lending.ini option) |

A fine is the daily rate for every day past the due date. A renewal runs a
fresh loan period from the day it is made.

## Loan limits

| key | value | meaning |
|---|---|---|
| `loan_limit.adult` | `20` | items an adult member may have on loan |
| `loan_limit.child` | `10` | items a child member may have on loan |

## Refusals

Every refusal has a stable code and a message.

| key | value | meaning |
|---|---|---|
| `unknown_member` | `no member with card {card}` | the card is not registered |
| `unknown_copy` | `no copy with barcode {barcode}` | the barcode is not in the catalogue |
| `unknown_title` | `no title with id {title}` | the title id is not in the catalogue |
| `duplicate_member` | `card {card} is already registered` | joining or importing a card that exists |
| `cannot_leave` | `{card} cannot leave: {reason}` | closing a membership with loans out or money owed |
| `invalid_member` | `member {card}: {problem}` | a member record fails its checks |
| `on_loan` | `{barcode} is already on loan` | lending a copy that is out |
| `not_on_loan` | `{barcode} is not on loan` | renewing, returning or writing off a copy that is not out |
| `not_in_transit` | `{barcode} is not in transit` | receiving a copy that is not travelling |
| `wrong_branch` | `{barcode} belongs to {branch}` | receiving a copy at a branch that is not its home |
| `held_for_other` | `{barcode} is being held for another member` | lending a copy set aside for someone else |
| `loan_limit` | `{card} has reached the loan limit of {limit}` | lending past the member's loan limit |
| `member_blocked` | `{card} owes {owed} and cannot borrow until it is paid` | lending to a member owing `block_at` or more |
| `renew_limit` | `{barcode} has already been renewed {limit} times` | renewing past `max_renewals` |
| `hold_limit` | `{card} already has {limit} holds` | placing a hold past `max_holds` |
| `duplicate_hold` | `{card} already has a hold on {title}` | placing a second hold on one title |
| `bad_waiver` | `cannot waive {amount}: {card} owes {owed}` | waiving nothing, or more than is owed |
| `bad_note` | `note not added: {problem}` | an empty or overlong note |
| `bad_amount` | `not an amount of money: {text}` | money that cannot be read, or a payment of nothing |
| `bad_date` | `not a date: {text}` | a date that is not YYYY-MM-DD |
| `bad_setting` | `lending.ini option {name}: {problem}` | a setting that cannot be used |
| `bad_catalogue` | `{path}: {problem}` | a catalogue record that cannot be used |
| `bad_calendar` | `{path} line {line}: {problem}` | a holidays line that is not a date |
| `bad_ledger` | `{path} line {line}: {problem}` | a ledger line that cannot be read |
| `bad_import` | `row {row}: {problem}` | a members CSV row that cannot be imported |

## The loans ledger

`loans.ledger` is plain text. The first line names the format; every other
line is one event, with tab-separated fields. Lines are only ever appended.

| key | value | meaning |
|---|---|---|
| `ledger_header` | `#lending-ledger v1` | first line of the loans ledger file |
| `ledger.fields` | `date event barcode card due amount` | the fields of each ledger line, in order (file) |
| `ledger.separator` | `tab` | what separates the fields of a ledger line (file) |
| `ledger.empty` | `-` | written in a ledger field that has no value (file) |
| `ledger.amount` | `2.50` | how amounts are written in the ledger: pounds, two decimals, no sign (file) |

The events:

| event | what it records |
|---|---|
| `checkout` | a copy lent; `due` is its due date; amount 0.00 |
| `renew` | a loan renewed; `due` is the new due date; amount 0.00 |
| `return` | a copy taken back; `due` is the date it was due; amount is the fine charged, 0.00 if none |
| `lost` | a loan written off; amount is the copy's price, charged to the member |
| `payment` | money taken from a member; no barcode or due date |
| `waive` | money owed written off by staff; no barcode or due date |

What a member owes is never stored: it is the charges (`return` and `lost`
amounts) less payments and waivers.

## Members CSV

`lend export FILE` writes every member; `lend import FILE` reads the same
columns, in any order, with extra columns ignored.

| key | value | meaning |
|---|---|---|
| `export.columns` | `card,name,email,type,born,joined` | header row of the members CSV file `lend export` writes |
| `export.born` | `YYYY-MM-DD` | how the born column is written in the members CSV file `lend export` writes |
| `export.joined` | `YYYY-MM-DD` | how the joined column is written in the members CSV file `lend export` writes |

## Command line

| key | value | meaning |
|---|---|---|
| `--library` | `.` | the library directory (CLI) |
| `--today` | `YYYY-MM-DD` | the desk date; required (CLI) |
| `--branch` | `(none)` | the branch the desk is at; returns of other branches' copies go into transit (CLI) |
| `--format` | `text` | report output: text, csv or json (CLI) |
| `cli.error` | `lend: {code}: {message}` | how the CLI prints a refusal, on stderr |
| `cli.error_status` | `1` | the CLI's exit status after a refusal |

## Notices

| key | value | meaning |
|---|---|---|
| `notice.courtesy` | `Due soon: {count} item(s)` | subject of the courtesy reminder (outbox file) |
| `notice.overdue` | `Overdue: {count} item(s)` | subject of an overdue reminder (outbox file) |
| `notice.hold_ready` | `Ready to collect: {title}` | subject of a hold-ready notice (outbox file) |

## Reports

| key | value | meaning |
|---|---|---|
| `overdue.columns` | `barcode,title,card,due,days,accrued` | columns of `lend overdue`; `accrued` is what the member would be charged if the copy came back today (CLI) |
| `loans.columns` | `barcode,title,due,overdue,renewals_left,renewable` | columns of `lend loans`; `renewable` says whether a renewal would be accepted today (CLI) |
| `status.can_borrow` | `can borrow: {count}` | last line of `lend status`: how many more items the member may borrow now (CLI) |
