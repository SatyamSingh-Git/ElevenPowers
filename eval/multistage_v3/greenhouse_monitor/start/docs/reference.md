# greenhouse reference

Every documented behaviour, one fact per row. The meaning column says where the
fact shows: the command line (CLI), a file in the data directory, or an API call.

## Command line

`greenhouse [--data DIR] --now YYYY-MM-DDTHH:MM:SS COMMAND [options]`

| key | value | meaning |
|---|---|---|
| `--data` | `.` | CLI: the data directory holding every file below |
| `--now` | `YYYY-MM-DDTHH:MM:SS` | CLI: the time the command runs at; required, there is no wall-clock default |
| `summary --date` | `today` | CLI: the day `summary` covers; `alerts`, `report`, `light`, `climate`, `weekly`, `uptime` and `digest` take the same option |
| `summary --format` | `text` | CLI: `text`, `csv` or `json`; the `report_format` setting changes the default |
| `status --format` | `text` | CLI: `text` or `json` |
| `schedule --start` | `06:00` | CLI: when the first valve opens; zones then run back to back |
| `trend --hours` | `3` | CLI: how far back `trend` looks |
| `alert-stats --days` | `7` | CLI: days counted, ending on `--date` |
| `archive --days` | `archive_after_days` | CLI: days kept in the readings log; defaults to the setting |
| `export --format` | `csv` | CLI: `csv` or `json` |
| `ingest output` | `imported {imported} rows, rejected {rejected}` | CLI: the line `ingest` prints, totalled over all files |
| `ingest problem` | `line {line}: {problem}` | CLI: printed to stderr for each rejected row, prefixed with the file name when several files are given |
| `record output` | `recorded {sensor} {kind} {value} {unit}` | CLI: the line `record` prints, value calibrated |
| `calibrate output` | `calibrated {sensor}: {offset:+.2f}` | CLI: the line `calibrate SENSOR OFFSET` prints |
| `calibrate --clear output` | `cleared {sensor}` | CLI: the line `calibrate SENSOR --clear` prints |
| `check output` | `{count} new alerts` | CLI: the last line `check` prints, after one line per new alert |
| `irrigate output` | `{zone}: {minutes} min ({reason})` | CLI: one line per zone with a moisture target |
| `schedule output` | `scheduled {count} valves` | CLI: the last line `schedule` prints |
| `error output` | `error: {message}` | CLI: printed to stderr when a command fails |
| `exit code on error` | `1` | CLI: exit status of a failed command; `validate` also exits 1 when it finds problems |

## Settings

`settings.json` in the data directory is optional and may name only the settings
a site changes.

| key | value | meaning |
|---|---|---|
| `stale_minutes` | `30` | settings.json: a sensor silent for longer raises `stale` |
| `minutes_per_point` | `2.0` | settings.json: irrigation minutes per point of moisture below target |
| `max_irrigation_minutes` | `30` | settings.json: longest irrigation suggested for one zone |
| `dry_margin` | `2.0` | settings.json: points below target tolerated without watering |
| `max_offset` | `5.0` | settings.json: largest calibration offset accepted |
| `report_format` | `text` | settings.json: default `summary --format` |
| `light_on_lux` | `10000.0` | settings.json: hourly mean illuminance counted as photoperiod |
| `ppfd_per_lux` | `0.0185` | settings.json: umol/m2/s of photon flux per lux |
| `target_dli` | `12.0` | settings.json: daily light integral below which a zone is marked short |
| `vpd_low_kpa` | `0.4` | settings.json: vapour pressure deficit below this is `low` |
| `vpd_high_kpa` | `1.6` | settings.json: vapour pressure deficit above this is `high` |
| `condensation_margin` | `2.0` | settings.json: air within this many C of its dew point is a condensation risk |
| `gap_minutes` | `20` | settings.json: silence longer than this counts as a reporting gap |
| `archive_after_days` | `90` | settings.json: days `archive` keeps in the readings log |

## Error messages

| key | value | meaning |
|---|---|---|
| `unknown zone` | `unknown zone: {zone}` | a zone not in layout.json: an ingest row, `record`, thresholds lookups |
| `unknown kind` | `unknown kind: {kind}` | a kind not in the sensor catalog |
| `unknown unit` | `unknown unit {unit} for {kind}` | a unit the catalog does not accept for the kind |
| `bad time` | `bad time: {value}` | an ingest row whose time is not `YYYY-MM-DDTHH:MM:SS` |
| `bad value` | `bad value: {value}` | an ingest row whose value is not a number |
| `missing sensor` | `missing sensor` | an ingest row or `record` without a sensor id |
| `out of range` | `out of range: {value} {unit}` | a calibrated value outside the catalog range |
| `duplicate reading` | `duplicate reading for {sensor}` | an ingest row repeating a sensor and time from the same file |
| `offset limit` | `offset too large: {offset}` | CLI: `calibrate` refusing an offset beyond `max_offset` |
| `no offset` | `no offset for {sensor}` | CLI: `calibrate --clear` for a sensor without an offset |
| `hand-held kind` | `{kind} cannot be entered by hand` | CLI: `record` with a kind the hand-held meters cannot read |
| `unknown setting` | `unknown setting: {name}` | settings.json naming a setting that does not exist |
| `setting type` | `setting {name} must be a number` | settings.json giving a numeric setting another type |
| `invalid date` | `invalid date: {value}` | CLI: a `--date` that is not `YYYY-MM-DD` |
| `unknown format` | `unknown format: {name}` | CLI: a `summary --format` with no renderer |
| `layout not found` | `layout not found: {file}` | any command that needs zones, without layout.json |
| `missing columns` | `{file}: expected columns {columns}` | CLI: `ingest` of an export lacking a required column |

## Files

| key | value | meaning |
|---|---|---|
| `readings.csv columns` | `timestamp,zone,sensor,kind,value,unit` | file: the readings log; values in the kind's canonical unit, calibration applied |
| `readings.csv timestamp` | `YYYY-MM-DDTHH:MM:SS` | file: the readings log's time format, greenhouse local time |
| `readings.csv sensor` | `as received` | file: the readings log's sensor ids, spelled as the controller or `record` gave them |
| `controller export columns` | `time,zone,sensor,kind,value,unit` | file: what `ingest` reads; column order free, extra columns ignored |
| `alerts.jsonl fields` | `at,zone,sensor,kind,code,value,limit,unit` | file: one JSON object per alert in the alerts log |
| `alerts.jsonl code` | `high, low, stale` | file: the alert codes the alerts log holds |
| `irrigation.csv columns` | `zone,minutes,reason` | file: the irrigation plan `irrigate` writes and `schedule` reads |
| `valves.txt line` | `{start} {valve} {zone} {minutes}` | file: one line per watered zone, start as HH:MM |
| `calibration.json` | `{"<sensor>": <offset>}` | file: offsets in the kind's canonical unit |
| `layout.json zone fields` | `id,name,crop,valve,target_moisture,area_m2,flow_lpm` | file: the first four are required |
| `summary json row fields` | `zone,kind,unit,count,min,max,mean` | CLI: each entry of `rows` in `summary --format json` |
| `status json fields` | `sensor,zone,kind,value,unit,at,stale` | CLI: each entry of `status --format json` |
| `archive file` | `archive/readings-YYYY-MM.csv` | file: where `archive` moves old readings |
| `digest file` | `outbox/digest-YYYY-MM-DD.txt` | file: what `digest` writes for the phone gateway |

## Sensor kinds

From the vendor catalog in `src/greenhouse/_generated.py`.

| key | value | meaning |
|---|---|---|
| `temperature` | `C` | canonical unit; accepts C and F; range -20.0 to 60.0; 1 decimal |
| `humidity` | `%` | canonical unit; accepts %; range 0 to 100; no decimals |
| `soil_moisture` | `%` | canonical unit; accepts %; range 0.0 to 100.0; 1 decimal |
| `light` | `lux` | canonical unit; accepts lux and klux; range 0 to 150000; no decimals |
