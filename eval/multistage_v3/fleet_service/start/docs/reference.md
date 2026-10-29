# fleetkeep reference

The facts other tools and people rely on. Money is in dollars with two decimals
wherever it is typed or printed; files keep it in whole cents.

## Settings

Read from the `[fleet]` section of `fleet.ini` in the fleet directory. A
setting left out takes its default.

| Setting | Default | Meaning |
|---|---|---|
| `name` | `fleet` | fleet.ini setting: the fleet's name |
| `labour_rate` | `95.00` | fleet.ini setting: hourly rate for labour charged without a rate of its own |
| `due_soon_miles` | `500` | fleet.ini setting: a service this many miles or fewer from due is `due-soon` |
| `due_soon_days` | `14` | fleet.ini setting: a service this many days or fewer from due is `due-soon` |
| `max_daily_miles` | `1000` | fleet.ini setting: most miles a day accepted between two odometer readings |

## Command line

Every command takes `--fleet` before the command name. `fleetkeep.cli.main.main(argv, clock)`
runs one command and returns its exit status.

| Option | Value | Meaning |
|---|---|---|
| `--fleet` | `.` | command line: fleet directory |
| `--format` | `table` | command line: default output format of report commands |
| `formats` | `table,csv,json` | command line: the values `--format` accepts |
| `--as-of` | `today` | command line: day `due`, `remind`, `vehicles`, `vehicle show`, `tyre list` and `check` report as of |
| `--on` | `today` | command line: day recorded by `odometer add`, `fuel add`, `wo open`, `wo close`, `vehicle retire`, `defect report` and `tyre add` |
| `exit status on error` | `1` | command line: a failed command prints `error: <code> <message>` to stderr |

### Report columns

Every report prints these columns in this order, in each format. JSON prints
money and decimals as strings, dates as `YYYY-MM-DD` and empty values as `null`.

| Report | Columns | Meaning |
|---|---|---|
| `fleetkeep due` | `vehicle,code,service,due_miles,remaining_miles,due_date,remaining_days,status` | command line: every service of every vehicle in service, `overdue` first, then `due-soon`, then `ok` |
| `fleetkeep costs` | `vehicle,miles,fuel,maintenance,total,cost_per_mile` | command line: maintenance is the total of each work order closed in the period, as `wo show` gives it |
| `fleetkeep fuel report` | `vehicle,fills,gallons,fuel_cost,miles,mpg` | command line: fuel bought and full-tank economy |
| `fleetkeep spend` | `month,fuel,orders,maintenance,total` | command line: spending by calendar month; maintenance as in `costs` |
| `fleetkeep downtime` | `vehicle,orders,days_down,breakdown_days,availability` | command line: days in the shop and availability percentage |
| `fleetkeep vehicles` | `id,class,make,model,year,odometer,last_reading,miles_per_day,retired` | command line: the vehicle list |
| `fleetkeep wo list` | `id,vehicle,status,opened,closed,services` | command line: work orders |
| `fleetkeep history show` | `date,code,service,odometer,order` | command line: one vehicle's service history |
| `fleetkeep defect list` | `id,vehicle,reported,severity,description,order,fixed` | command line: inspection defects |
| `fleetkeep parts stock` | `number,description,on_hand,unit_cost,value` | command line: parts on hand at average cost |
| `fleetkeep catalog` | `code,service,miles,months,classes` | command line: the service catalog |
| `fleetkeep summary` | `vehicle,miles,total,cost_per_mile,mpg,days_down,availability` | command line: one line per vehicle, each figure as `costs`, `fuel report` and `downtime` give it |

Statuses: a service is `overdue` once its miles or its date have passed,
`due-soon` within `due_soon_miles` or `due_soon_days` of either, and `ok`
otherwise. `fleetkeep remind` prints one line for every service that is not
`ok`.

## Rounding

| Figure | Places | Meaning |
|---|---|---|
| `cost_per_mile` | `3` | command line: `costs`, rounded half up |
| `mpg` | `1` | command line: `fuel report`, rounded half up |
| `availability` | `1` | command line: `downtime`, percentage rounded half up |
| `labour amount` | `0.01` | library: hours times rate, rounded half up to the cent |

## Limits

| Limit | Value | Meaning |
|---|---|---|
| `max_fill_gallons` | `150` | limit: largest fill-up accepted by `fuel add` and by fuel-card import |
| `min_model_year` | `1980` | limit: earliest model year accepted by `vehicle add` and vehicle import |
| `max_labour_hours` | `24` | limit: most hours on one labour line, from `wo labour` or a timesheet |
| `vehicle id` | `^[A-Z]{2,4}-[0-9]{3,4}$` | limit: vehicle ids, after upper-casing what was typed |
| `vehicle classes` | `light,medium,heavy` | limit: classes a vehicle can have |
| `defect severities` | `minor,out-of-service` | limit: an open `out-of-service` defect grounds its vehicle |
| `tyre positions` | `LF,RF,LR,RR,LRO,LRI,RRO,RRI` | limit: wheel positions for tread readings |
| `stale order days` | `14` | command line: `check` reports work orders open longer than this |
| `reading gap days` | `30` | command line: `check` reports vehicles with no reading for longer than this |
| `min tread` | `4` | command line: `check` reports tread below this many 32nds of an inch |

## Fleet directory files

| File | Fields | Meaning |
|---|---|---|
| `fleet.ini` | `[fleet]` | file: settings, in one section |
| `vehicles.json` | `id,class,make,model,year,in_service,start_odometer,retired` | file: one object per vehicle |
| `workorders.json` | `id,vehicle,opened,closed,services,parts,labour,note,breakdown` | file: one object per work order; amounts in cents |
| `odometer.csv` | `vehicle,date,odometer` | file: header row of the odometer log |
| `fuel.csv` | `vehicle,date,gallons,cost,odometer` | file: header row of the fuel log; cost in cents |
| `history.csv` | `vehicle,code,date,odometer,order` | file: header row of the service history |
| `cards.csv` | `card,vehicle` | file: fuel cards and the vehicle each one fills |
| `tread.csv` | `vehicle,date,position,depth` | file: tread readings in 32nds of an inch |
| `parts.json` | `number,description,on_hand,unit_cost` | file: one object per stocked part |
| `defects.json` | `id,vehicle,reported,description,severity,order,fixed` | file: one object per defect |

## Import files

| Import | Columns | Meaning |
|---|---|---|
| `fuel import` | `Card,Unit,Date,Gallons,Amount,Odometer` | file: the fuel-card provider's export; a blank `Unit` uses the card's vehicle |
| `fuel import date` | `MM/DD/YYYY` | file: date format of the fuel-card export |
| `history import` | `vehicle,code,date,odometer` | file: service history from the previous system; unknown codes are skipped |
| `timesheet import` | `order,mechanic,hours,rate` | file: mechanics' timesheets; a blank rate means the labour rate, as `wo labour` charges it |
| `odometer import` | `vehicle,timestamp,odometer` | file: telematics reports; the last report of each day is kept |
| `vehicle import` | `id,class,make,model,year,in_service,odometer` | file: the leasing company's delivery schedule |

Every import prints `imported N, skipped N, rejected N`, then one
`line <n>: skipped: <reason>` or `line <n>: rejected: <error>` per row.

## Errors

Raised by the library as `FleetError` with these codes; the command line prints
them as `error: <code> <message>`.

| Code | Message | Meaning |
|---|---|---|
| `E101` | `invalid vehicle id: {vehicle}` | error raised by the library and printed by the CLI |
| `E102` | `unknown vehicle class: {vehicle_class}` | error raised by the library and printed by the CLI |
| `E103` | `unknown vehicle: {vehicle}` | error raised by the library and printed by the CLI |
| `E104` | `vehicle already exists: {vehicle}` | error raised by the library and printed by the CLI |
| `E105` | `odometer went backwards for {vehicle}: {value} is below {previous}` | error raised by the library and printed by the CLI |
| `E106` | `odometer jump too large for {vehicle}: {miles} miles in {days} days` | error raised by the library and printed by the CLI |
| `E107` | `reading for {vehicle} on {day} is before its latest reading on {latest}` | error raised by the library and printed by the CLI |
| `E108` | `model year {year} is outside {earliest}-{latest}` | error raised by the library and printed by the CLI |
| `E109` | `vehicle {vehicle} cannot retire before it entered service on {in_service}` | error raised by the library and printed by the CLI |
| `E111` | `fill-up must be more than zero gallons: {gallons}` | error raised by the library and printed by the CLI |
| `E112` | `fill-up of {gallons} gallons is over the limit of {limit}` | error raised by the library and printed by the CLI |
| `E113` | `fuel card {card} is not assigned to a vehicle` | error raised by the library and printed by the CLI |
| `E121` | `unknown work order: {order}` | error raised by the library and printed by the CLI |
| `E122` | `cannot change closed work order {order}` | error raised by the library and printed by the CLI |
| `E123` | `work order {order} cannot close before it opened on {opened}` | error raised by the library and printed by the CLI |
| `E124` | `service {code} does not apply to {vehicle_class} vehicles` | error raised by the library and printed by the CLI |
| `E125` | `only an open work order with no charges can be cancelled: {order}` | error raised by the library and printed by the CLI |
| `E131` | `not enough {number} in stock: {on_hand} on hand` | error raised by the library and printed by the CLI |
| `E132` | `no price given for unstocked part {number}` | error raised by the library and printed by the CLI |
| `E133` | `part {number} is not stocked` | error raised by the library and printed by the CLI |
| `E141` | `invalid amount: {text}` | error raised by the library and printed by the CLI |
| `E142` | `invalid date: {text}` | error raised by the library and printed by the CLI |
| `E143` | `invalid number: {text}` | error raised by the library and printed by the CLI |
| `E144` | `period ends before it starts: {start} to {end}` | error raised by the library and printed by the CLI |
| `E145` | `{path} is missing columns: {columns}` | error raised by the library and printed by the CLI |
| `E146` | `no reading for {vehicle} on {day}` | error raised by the library and printed by the CLI |
| `E151` | `unknown setting in fleet.ini: {name}` | error raised by the library and printed by the CLI |
| `E152` | `invalid value for {name}: {value}` | error raised by the library and printed by the CLI |
| `E153` | `no fleet in {path}` | error raised by the library and printed by the CLI |
| `E154` | `a fleet already exists in {path}` | error raised by the library and printed by the CLI |
| `E161` | `unknown defect: {defect}` | error raised by the library and printed by the CLI |
| `E162` | `unknown defect severity: {severity}` | error raised by the library and printed by the CLI |
| `E163` | `defect {defect} is already fixed` | error raised by the library and printed by the CLI |
| `E164` | `defect {defect} is not on {vehicle}` | error raised by the library and printed by the CLI |
| `E171` | `tyre position must be one of {positions}: {position}` | error raised by the library and printed by the CLI |
| `E172` | `tread depth must be 0-32 (32nds of an inch): {depth}` | error raised by the library and printed by the CLI |
