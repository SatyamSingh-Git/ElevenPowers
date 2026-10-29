# Box office reference

Everything here is behaviour other people rely on: the counter staff, finance,
and the scripts that read our files. Amounts are always whole pence unless a
row says otherwise; the command line prints them as pounds and pence.

## Settings

Read from the `[boxoffice]` section of `boxoffice.ini` in the data directory.
A setting that is not in the file takes its default. An unknown setting is an
error, so a typo is not silently ignored.

| key | default | meaning |
|---|---|---|
| `theatre` | `Box Office` | setting: name printed on receipts, tickets and letters |
| `currency` | `GBP` | setting: currency named on receipts |
| `booking_fee` | `150` | setting: pence charged once per order, whatever the number of seats; never refunded unless the performance is cancelled |
| `hold_minutes` | `15` | setting: how long a hold keeps its seats |
| `max_tickets_per_order` | `10` | setting: most seats in one hold, and so in one order |
| `refund_cutoff_hours` | `48` | setting: refunds and exchanges close this many hours before the performance starts |

## Command line

`python -m boxoffice [--data DIR] [--now TIME] COMMAND ...`. Run with `--help`
for every command. Errors go to standard error.

| key | value | meaning |
|---|---|---|
| `--data` | `.` | CLI: the data directory |
| `--now` | `YYYY-MM-DDTHH:MM` | CLI: act at this time instead of the system clock |
| `--format` | `text` | CLI: default output format of reports and listings |
| `formats` | `text, csv, json, markdown` | CLI: what `--format` accepts; json keeps money in pence |
| `--payment` | `card` | CLI: default payment method for `sell` |
| `cli.error` | `error: {message}` | CLI: how a refused request is reported, on standard error |
| `cli.exit_error` | `1` | CLI: exit status of a refused request |
| `hold.output` | `hold {hold}: {seats} until {expires}` | CLI: printed by `hold` |
| `sell.output` | `order {order}: {tickets} tickets, total {total}` | CLI: printed by `sell` |
| `refund.output` | `refunded {amount} on order {order}` | CLI: printed by `refund` |
| `exchange.output` | `exchanged order {order} to {code}: settled {amount}` | CLI: printed by `exchange`; a negative amount is paid back to the customer |

Seat arguments accept runs along a row: `A1-A4` means A1, A2, A3 and A4.

## Python API

`BoxOffice(data_dir, clock)` from `boxoffice.services.boxoffice` wires every
service to one data directory and one clock (`boxoffice.clock.FixedClock`).

- `office.holds.place(code, seats)` and `office.holds.place_best(code, count, section=None)` return a `Hold`.
- `office.sales.checkout(hold_id, concessions=None, payment="card", customer=None)` returns an `Order`; `concessions` maps a seat to a concession name.
- `office.refunds.refund(order_id, seats=None)` returns the pence paid back; `None` refunds the whole order.
- `office.refunds.exchange(order_id, code, seats)` moves every seat of an order and returns the pence the customer pays, negative when they are paid back.
- `office.seat_states(code)` maps every seat id to its state.

Refusals raise `boxoffice.errors.BoxOfficeError`, whose `code` is one of the
errors listed below and whose message is the text beside it.

## Pricing and checkout

A concession takes a percentage off the face value of the seat's tier.

| key | value | meaning |
|---|---|---|
| `adult` | `0` | concession: percent off face value |
| `child` | `50` | concession: percent off face value |
| `senior` | `20` | concession: percent off face value |
| `student` | `25` | concession: percent off face value |
| `concession_rounding` | `1` | concession prices are a multiple of this many pence; the discount itself rounds half up |
| `payment_methods` | `card, cash` | payment methods accepted at checkout |
| `order_id` | `B0001` | order references: B and four digits, issued in sequence |
| `hold_id` | `H0001` | hold references: H and four digits, issued in sequence |

## Seats

| key | value | meaning |
|---|---|---|
| `seat_states` | `free, held, sold` | the states the `seat_states` API call reports for a seat |
| `plan.free` | `.` | CLI seat plan (`seats`): symbol for a free seat |
| `plan.held` | `h` | CLI seat plan (`seats`): symbol for a held seat |
| `plan.sold` | `x` | CLI seat plan (`seats`): symbol for a sold seat |

The seat plan (`seats`) prints one line per row: the row, the number of its
first seat, then one symbol per seat. Best available searches sections and rows
in seat-map order and holds the first run of free seats side by side.

## Seat map file

`venue.txt` in the data directory, installed with the `venue` command.

| key | value | meaning |
|---|---|---|
| `venue` | `venue NAME` | seat map file: the first line |
| `section` | `section NAME tier=T` | seat map file: starts a section; its rows follow |
| `row` | `row R FIRST-LAST [CODE:N,N]` | seat map file: a row of seats, with access codes for some of them |
| `C` | `companion seat` | seat map file: access code |
| `H` | `hearing loop` | seat map file: access code |
| `R` | `restricted view` | seat map file: access code |
| `W` | `wheelchair space` | seat map file: access code |

## Ledger file

`ledger.jsonl` in the data directory: one JSON object per line, appended and
never rewritten. A `sale` entry is money taken for an order; a `refund` entry
is money paid back. An exchange is recorded as a `refund` of the old seats
followed by a `sale` of the new ones. Each entry also names its `order`,
`performance` and `payment` method.

| key | value | meaning |
|---|---|---|
| `date` | `YYYY-MM-DD` | ledger file: when the entry was recorded |
| `amount` | `pence` | ledger file: money taken is positive, money paid back negative |
| `tickets` | `count` | ledger file: how many seats the entry covers |

## Reports and exports

| key | value | meaning |
|---|---|---|
| `daily.columns` | `day, sold, returned, sales, refunds, net` | CLI `report daily`: one row per day; `net` is every ledger amount of the day added up |
| `cashup.columns` | `payment, entries, amount` | CLI `report cashup`: one row per payment method, then a total |
| `occupancy.columns` | `section, capacity, sold, occupancy` | CLI `report occupancy`: one row per section, then `all` |
| `export.columns` | `order, performance, seat, concession, price, refunded, payment` | orders CSV file written by `export` |

The price list (`prices`) shows, for each tier, what a seat costs at each
concession: the same prices checkout charges.

## Errors

| key | message | meaning |
|---|---|---|
| `bad-seatmap` | `seat map line {line}: {problem}` | the seat map cannot be read |
| `no-venue` | `no venue installed; run the venue command first` | nothing can be sold before a venue exists |
| `unknown-section` | `unknown section {section}` | best available was asked for a section the venue lacks |
| `unknown-seat` | `unknown seat {seat}` | seat id not in the venue |
| `duplicate-seat` | `seat {seat} is named twice` | the same seat given twice in one request |
| `seat-unavailable` | `seat {seat} is not available` | seat already held or sold |
| `bad-performance-code` | `performance codes use A-Z, 0-9 and '-', got {code}` | performance code refused |
| `unknown-performance` | `unknown performance {code}` | no such performance |
| `duplicate-performance` | `performance {code} already exists` | performance code taken |
| `performance-has-orders` | `performance {code} has orders; cancel it instead` | only a performance without orders can be removed |
| `missing-price` | `performance {code} has no price for tier {tier}` | every tier of the venue needs a price |
| `unknown-tier` | `the venue has no tier {tier}` | repricing a tier the venue lacks |
| `performance-started` | `performance {code} has already started` | no holds or exchanges into a performance once it starts |
| `performance-cancelled` | `performance {code} is cancelled` | nothing more can be sold for it |
| `no-seats` | `name at least one seat` | an empty hold |
| `too-many` | `at most {limit} tickets per order` | more seats than `max_tickets_per_order` |
| `not-enough-seats` | `no block of {count} seats available` | best available found no run long enough |
| `unknown-hold` | `unknown hold {hold}` | no such hold |
| `hold-expired` | `hold {hold} has expired` | the hold ran out before checkout |
| `hold-closed` | `hold {hold} is no longer active` | the hold was released or already sold |
| `not-in-hold` | `seat {seat} is not in hold {hold}` | a concession named for a seat the hold lacks |
| `unknown-concession` | `unknown concession {name}` | no such concession |
| `unknown-payment` | `unknown payment method {name}` | payment method not accepted |
| `unknown-order` | `unknown order {order}` | no such order |
| `not-in-order` | `seat {seat} is not in order {order}` | refunding a seat the order lacks |
| `refund-closed` | `refunds close {hours} hours before the performance` | too late to refund or exchange |
| `seat-count` | `an exchange needs {count} seats` | an exchange names one new seat per seat of the order |
| `exchange-refunded` | `order {order} has refunded seats and cannot be exchanged` | exchanges move whole orders only |
| `bad-email` | `not an email address: {email}` | customer email refused |
| `unknown-customer` | `no customer with email {email}` | no such customer |
| `duplicate-customer` | `a customer with email {email} already exists` | email already in the customer book |
| `already-waiting` | `{email} is already waiting for {code}` | joining a waiting list twice |
| `not-waiting` | `{email} is not waiting for {code}` | leaving a waiting list one is not on |
| `unknown-backup` | `no backup named {name}` | restoring a backup that does not exist |
| `backup-exists` | `a backup named {name} already exists` | backups are never overwritten |
