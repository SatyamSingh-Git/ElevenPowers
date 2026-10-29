# hoteldesk reference

The facts the desk depends on. Amounts are written `0.00` unless a row says
otherwise; inside the program they are integer cents.

## Settings

Read from the settings file (`--settings`); a setting the file leaves out keeps
its default.

| Key | Default | Meaning |
|---|---|---|
| `check_in_time` | `15:00` | Setting: the time rooms are promised from |
| `check_out_time` | `11:00` | Setting: checking out after this time on the business date posts the late check-out fee |
| `max_stay_nights` | `30` | Setting: the longest stay a booking, quote, extension or channel import accepts |
| `weekend_uplift_percent` | `10` | Setting: added to the rate of Friday and Saturday nights |
| `late_checkout_fee` | `25.00` | Setting: the amount posted as `LCO` on a late check-out |
| `journal_file` | `audit_journal.csv` | Setting: name of the audit journal file, kept beside the state file |
| `currency` | `USD` | Setting: the currency every amount is in |

## Command line

| Key | Value | Meaning |
|---|---|---|
| `--state` | `hotel-state.json` | CLI: the state file every command loads and saves |
| `--settings` | `hotel.json` | CLI: the settings file; when it does not exist every setting has its default |
| `--now` | `business date 10:00` | CLI: the time a command acts at when `--now` is not given |
| `book --plan` | `BAR` | CLI: rate plan when none is given (also the API default of `book`) |
| `book --adults` | `1` | CLI: adults when not given |
| `pay --method` | `card` | CLI: payment method when not given |
| `report --format` | `text` | CLI: report format when not given; `json` and `csv` are the others |
| `report --date` | `business date` | CLI: the day a report covers when not given |
| `wake-up due --minutes` | `15` | CLI: how far ahead due wake-up calls are listed |
| `report names` | `arrivals, availability, departures, forecast, housekeeping, inhouse, ledger, occupancy, payments` | CLI: the reports `report` can print |
| `exit.ok` | `0` | CLI: exit status when the command succeeded |
| `exit.refused` | `1` | CLI: exit status when the desk refused the command; the message goes to stderr |
| `exit.usage` | `2` | CLI: exit status for arguments argparse cannot read |
| `error.format` | `error: {message}` | CLI: how a refusal is printed on stderr |

## Messages

Raised as `HotelError` subclasses by the API calls named, and printed by the CLI
in the `error.format` above.

| Key | Message | Meaning |
|---|---|---|
| `error.guest_required` | `Guest name is required` | API `book` and the CLI: blank guest name |
| `error.unknown_room_type` | `Unknown room type: {code}` | API and CLI: no such room type |
| `error.unknown_rate_plan` | `Unknown rate plan: {code}` | API and CLI: no such rate plan |
| `error.unknown_room` | `Unknown room: {number}` | API and CLI: no such room |
| `error.no_reservation` | `No reservation {id}` | API and CLI: no such reservation |
| `error.departure` | `Departure must be after arrival` | API `book`/`quote` and the CLI |
| `error.arrival_past` | `Arrival {arrival} is before the business date {business_date}` | API `book`/`quote` and the CLI |
| `error.max_stay` | `Stays are limited to {max_stay_nights} nights` | API `book`/`quote`/`extend_stay` and the CLI |
| `error.min_nights` | `Rate plan {plan} requires at least {min_nights} nights` | API `book`/`quote` and the CLI |
| `error.adults` | `Room type {type} holds at most {max_adults} adults` | API `book`/`quote` and the CLI |
| `error.sold_out` | `No {type} rooms available on {date}` | API `book` and the CLI: a night of the stay has no room left |
| `error.cannot_cancel` | `Reservation {id} is {status} and cannot be cancelled` | API `cancel` and the CLI |
| `error.not_arriving` | `Reservation {id} arrives on {arrival}` | API `check_in` and the CLI: check-in before the arrival date |
| `error.room_occupied` | `Room {room} is occupied` | API `check_in` and the CLI: the chosen room has a guest in it |
| `error.room_not_ready` | `Room {room} is not available` | API `check_in` and the CLI: the chosen room is not clean or inspected |
| `error.no_ready_room` | `No {type} room is ready` | API `check_in` and the CLI: no room was chosen and none of the type is ready |
| `error.not_in_house` | `Reservation {id} is not in house` | API `post_charge`/`check_out` and the CLI |
| `error.balance_due` | `Balance due: {balance}` | API `check_out` and the CLI: the folio is not settled |
| `error.unknown_charge_code` | `Unknown charge code: {code}` | API `post_charge` and the CLI `post` |
| `error.payment_method` | `Unknown payment method: {method}` | API `post_payment` |
| `error.overpayment` | `Payment of {amount} is more than the balance of {balance}` | API `post_payment` and the CLI `pay` |
| `error.unknown_status` | `Unknown housekeeping status: {status}` | API `set_status` and the CLI `hk` |
| `error.unknown_setting` | `Unknown setting: {name}` | Settings file: a key the program does not know |

## Charges and tax

Codes are case-insensitive on the way in and stored upper case.

| Key | Code | Meaning |
|---|---|---|
| `charge.room` | `RM` | Folio and CLI `post`: code of the nightly room charge the night audit posts |
| `charge.tax` | `TAX` | Folio: tax posted alongside a taxable charge |
| `charge.late_checkout` | `LCO` | Folio: late check-out fee |
| `charge.food` | `FB` | Folio: food and beverage |
| `charge.minibar` | `MB` | Folio: minibar |
| `charge.parking` | `PK` | Folio: parking |
| `charge.phone` | `PH` | Folio: telephone, tax exempt |
| `tax.lodging` | `11.75%` | Folio: tax on `RM` and `LCO` charges |
| `tax.sales` | `7.25%` | Folio: tax on `FB`, `MB` and `PK` charges |
| `tax.rounding` | `down` | Folio: how the tax on each charge is rounded to a whole cent |
| `quote.tax` | `same as posted` | API `quote` and CLI `quote`: the tax quoted equals the tax the night audit will post for the stay |

## Records and files

| Key | Value | Meaning |
|---|---|---|
| `reservation.number` | `R{number:04d}` | API and CLI: reservations are numbered in booking order from `R0001`; a number is never reused |
| `reservation.statuses` | `booked, in_house, checked_out, cancelled, no_show` | API and state file |
| `housekeeping.statuses` | `clean, dirty, inspected, out_of_order` | API, CLI `hk` and state file |
| `payment.methods` | `card, cash, transfer` | API `post_payment` and CLI `pay --method` |
| `checkin.room_choice` | `lowest-numbered ready room` | API `check_in` and CLI `checkin`: the room given when none is chosen |
| `state.format` | `1` | State file: the `format` field |
| `journal.columns` | `business_date,rooms_sold,rooms_available,room_revenue,tax_revenue,other_revenue,payments` | File `audit_journal.csv`: header line; one line per audited business date |
| `journal.amounts` | `cents` | File `audit_journal.csv`: how the four money columns are written |
| `folio_export.columns` | `reservation,guest,date,code,description,amount` | File written by `export-folios`: header line |
| `channel_import.columns` | `channel_ref,guest,room_type,arrival,departure,adults,rate_plan` | File read by `import`: required header columns |
| `statistics.occupancy` | `fraction` | API `day_statistics()` and CLI `report occupancy --format json`: occupancy as a share of available rooms, `0.5` for half |
| `occupancy.days` | `7` | CLI `report occupancy`: days shown from the report date |
| `availability.days` | `14` | CLI `report availability`: days shown |
| `forecast.days` | `30` | CLI `report forecast`: days shown |
| `backups.keep` | `14` | Files in `backups/`: state copies kept, one taken before each night audit |
| `lost_items.hold_days` | `90` | API `dispose_unclaimed` and the night audit: days unclaimed property is held |
