# clinicbook reference

Every value below is what the code does today. The first column is the name
used in this reference, the second the value, the third what it is for and
where it shows up.

## Settings

Set in the `settings` block of the clinic file. Anything left out takes the
default shown here.

| key | default | meaning |
|---|---|---|
| `slot_minutes` | `20` | setting in the clinic file: length of every appointment, in minutes; slots run back to back from opening time |
| `no_show_fee` | `25.00` | setting in the clinic file: amount charged for each no-show |
| `reminder_lead_hours` | `24` | setting in the clinic file: a booking's reminder is due this many hours before it starts |
| `booking_horizon_days` | `60` | setting in the clinic file: how many days ahead bookings open |
| `currency` | `GBP` | setting in the clinic file: one of GBP, EUR or USD; amounts are shown with its symbol |

## Clinic file

| key | value | meaning |
|---|---|---|
| `clinic_file.name` | `clinic.json` | clinic file the CLI reads unless `--clinic` names another |
| `clinic_file.hours` | `09:00-17:00` | how the clinic file writes one weekday's opening hours; `null` means closed all day |
| `clinic_file.days` | `mon, tue, wed, thu, fri` | working days of a practitioner whose entry in the clinic file has no `days` |
| `holidays` | `england-and-wales` | public holidays the clinic is shut on, from the gov.uk bank holidays feed |
| `error.unknown_setting` | `unknown setting: {name}` | ConfigError from loading a clinic file with a setting not listed above |
| `error.shortest_slot` | `setting slot_minutes must be at least 5` | ConfigError from loading a clinic file with shorter slots |
| `error.currency` | `unsupported currency: {currency}` | ConfigError from loading a clinic file with another currency |

## Booking statuses

The `status` column of the bookings file holds one of these.

| status | value | meaning |
|---|---|---|
| `booked` | `booked` | status in the bookings file: the appointment is still to come, or not yet marked |
| `attended` | `attended` | status in the bookings file: the patient came |
| `no_show` | `no_show` | status in the bookings file: the patient did not come; charged `no_show_fee` |
| `cancelled` | `cancelled` | status in the bookings file: cancelled; the slot is free again and nothing is charged |

## Bookings file

| key | value | meaning |
|---|---|---|
| `bookings_file.name` | `bookings.csv` | bookings file the CLI reads and writes unless `--bookings` names another |
| `bookings_file.columns` | `id,patient,phone,practitioner,room,day,start,minutes,status,created` | header row of the bookings file |
| `bookings_file.order` | `day, start` | row order of the bookings file (ties go by practitioner) |
| `bookings_file.start` | `09:00` | how the start column of the bookings file writes a time: 24-hour HH:MM |
| `booking_reference` | `B0001` | booking references: `B` and a running number of at least four digits, never reused |

## Day schedule export

Written by `clinic schedule DAY`. The `utilisation` command reads it back.

| key | value | meaning |
|---|---|---|
| `export.name` | `schedule-{day}.csv` | file the CLI `schedule` command writes unless `--out` names another |
| `export.columns` | `date,start,end,practitioner,room,patient,phone,status` | header row of the exported day schedule file; the status column holds a label such as Booked |
| `export.time_format` | `%H:%M` | strftime format of the start and end columns in the exported day schedule file |
| `export.date_format` | `%Y-%m-%d` | strftime format of the date column in the exported day schedule file |

## Charges file

Written by `clinic fees --out FILE`. The `statement` command reads it back.

| key | value | meaning |
|---|---|---|
| `charges_file.name` | `charges.csv` | charges file the CLI `statement` command reads unless `--charges` names another |
| `charges_file.columns` | `booking,patient,phone,day,reason,amount` | header row of the charges file; amount is pounds and pence, e.g. 25.00 |
| `charges.reason` | `no-show` | reason column of the charges file for a no-show |

## Reminders and the outbox

| key | value | meaning |
|---|---|---|
| `outbox_file.name` | `outbox.csv` | outbox file the CLI `reminders` command appends to unless `--outbox` names another |
| `outbox_file.columns` | `booking,phone,send_at,text` | header row of the outbox file the SMS gateway collects |
| `reminder.text` | `{patient}, a reminder of your appointment with {practitioner} at {time} on {day}. Reply C to cancel.` | text of a reminder; the patient's first name, time as 09:00, day as Monday 02 March |

## Other files

| key | value | meaning |
|---|---|---|
| `waitlist_file.name` | `waitlist.json` | waiting-list file the CLI reads and writes unless `--waitlist` names another |
| `audit_file.name` | `audit.log` | audit log the CLI keeps beside the bookings file |
| `backups.folder` | `.backups` | folder beside the bookings file where the CLI copies it before each change |
| `backups.keep` | `20` | how many backups of the bookings file the CLI keeps |
| `partner_file.columns` | `Date,Time,Clinician,Client,Mobile` | header row the CLI `import` command expects from the booking partner |

## Limits

| key | value | meaning |
|---|---|---|
| `patient_name.max_length` | `60` | longest patient name `Desk.book` and the CLI `book` command accept |
| `series.max_weeks` | `12` | longest course `book_series` and the CLI `book --weeks` accept |

## Booking errors

Raised by `Desk.book` and the other `Desk` calls; the CLI prints them as
`error: <message>` and exits with status 1.

| key | value | meaning |
|---|---|---|
| `error.name` | `patient name is required` | error from `Desk.book` and the CLI `book` command for an empty name |
| `error.name_length` | `patient name is longer than 60 characters` | error from `Desk.book` and the CLI `book` command for a long name |
| `error.phone` | `invalid phone number` | error from `Desk.book` and the CLI `book` command for a phone number that is not eleven digits starting with 0 |
| `error.past` | `cannot book in the past` | error from `Desk.book` and the CLI `book` command |
| `error.horizon` | `bookings open {days} days ahead` | error from `Desk.book` and the CLI `book` command past `booking_horizon_days` |
| `error.closed` | `clinic is closed on {day}` | error from `Desk.book` and the CLI `book` command; day as 2026-03-02 |
| `error.not_working` | `{practitioner} does not work on {weekday}s` | error from `Desk.book` and the CLI `book` command |
| `error.outside_hours` | `{time} is outside opening hours` | error from `Desk.book` and the CLI `book` command when the appointment would start before opening or end after closing |
| `error.not_slot_start` | `{time} is not a slot start` | error from `Desk.book` and the CLI `book` command |
| `error.practitioner_busy` | `{practitioner} is already booked at {time}` | error from `Desk.book` and the CLI `book` command |
| `error.room_busy` | `room {room} is already booked at {time}` | error from `Desk.book` and the CLI `book` command |
| `error.no_booking` | `no booking {booking}` | error from any `Desk` call or CLI command given an unknown reference |
| `error.no_practitioner` | `no practitioner {practitioner}` | error from any `Desk` call or CLI command given an unknown practitioner |
| `error.not_booked` | `booking {booking} is {status}` | error from `Desk.cancel`, `Desk.mark_attended` and `Desk.mark_no_show` (and the CLI `cancel`, `attend` and `no-show` commands) once a booking has left `booked` |
| `error.not_started` | `booking {booking} has not started yet` | error from `Desk.mark_attended` and `Desk.mark_no_show` (and the CLI `attend` and `no-show` commands) before the start time |

## Command line

| key | value | meaning |
|---|---|---|
| `cli.error` | `error: {message}` | how the CLI prints any error, on stderr |
| `exit.error` | `1` | CLI exit status after an error |
| `exit.usage` | `2` | CLI exit status for arguments it cannot parse |
| `cli.booked` | `Booked {booking} for {patient} at {time} on {day}` | line the CLI `book` command prints per booking |
| `cli.cancelled` | `Cancelled {booking}` | line the CLI `cancel` command prints |
| `cli.attended` | `Marked {booking} attended` | line the CLI `attend` command prints |
| `cli.no_show` | `Marked {booking} as no-show` | line the CLI `no-show` command prints |
| `cli.no_slots` | `No free slots` | line the CLI `slots` and `next` commands print when nothing is free |
| `cli.schedule_written` | `Wrote {count} appointments to {path}` | line the CLI `schedule` command prints |
| `cli.fees_total` | `Total: {amount}` | last line of the CLI `fees` command, and of `statement` |
| `cli.fees_due` | `Fees due: {amount}` | last line of the CLI `summary` command: that day's no-show charges, the same total `fees` lists for that day |
| `slots --days` | `7` | default number of days the CLI `slots` command lists |
| `hours --days` | `28` | default number of days the CLI `hours` command looks ahead for closures |
| `stranded --days` | `60` | default number of days the CLI `stranded` command looks ahead |
| `sheets --folder` | `sheets` | default folder the CLI `sheets` command writes to |
