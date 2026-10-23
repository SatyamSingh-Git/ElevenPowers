# cronish reference

## Fields

An expression has five fields separated by spaces. Each field takes `*`, a
number, a name (months and weekdays only, any case), a range `a-b`, a step
`*/n`, `a-b/n` or `a/n` (from `a` to the end of the field), or a
comma-separated list of these.

| Field | Range | Meaning |
|---|---|---|
| `minute` | `0-59` | minute of the hour |
| `hour` | `0-23` | hour of the day, 24-hour clock |
| `day` | `1-31` | day of the month |
| `month` | `1-12` | month; `jan` to `dec` are accepted too |
| `weekday` | `0-6` | day of the week, 0 is Sunday; `sun` to `sat` are accepted too |

## Shortcuts

An expression may instead be one of these names, in any case.

| Shortcut | Expands to | Meaning |
|---|---|---|
| `@yearly` | `0 0 1 1 *` | midnight on 1 January |
| `@monthly` | `0 0 1 * *` | midnight on the first of every month |
| `@weekly` | `0 0 * * 0` | midnight at the start of Sunday |
| `@daily` | `0 0 * * *` | every midnight |
| `@hourly` | `0 * * * *` | on the hour |

## Planning

| Setting | Value | Meaning |
|---|---|---|
| `count` | `5` | runs listed by `next_runs`, `upcoming` and `--count` when no count is given |
| `max_count` | `100` | the most runs one call may ask for |
| `horizon_years` | `5` | how far ahead, or back, the planner searches before giving up |
| `first_run` | `at or after now` | where `next_runs` and `upcoming` start; a run in the minute `now` falls exactly on is listed |
| `last_run` | `at or before now` | what `previous_run` and `cronish last` return |
| `window` | `start inclusive, end exclusive` | the window `runs_between`, `overlaps` and `cronish between` use |
| `day_rule` | `either when both restricted` | when day and weekday are both restricted, a day matching either one runs |

## Errors

`ScheduleError` is a `ValueError`. Its message is `<field>: <problem>`, or
just the problem when no single field is to blame.

| Error | Message | When |
|---|---|---|
| `error.fields` | `expression: expected 5 fields, got {count}` | wrong number of fields |
| `error.shortcut` | `expression: unknown shortcut '{name}'` | an `@` name that is not a shortcut |
| `error.range` | `{field}: value {value} out of range {low}-{high}` | a number outside the field's range |
| `error.backwards` | `{field}: range {range} runs backwards` | a range whose start is after its end |
| `error.name` | `{field}: unknown name '{name}'` | a word that is not a month or weekday name |
| `error.syntax` | `{field}: cannot parse '{text}'` | anything else the field cannot read |
| `error.never` | `day: no selected month has a day {day}` | validation only: the day never occurs in the chosen months |
| `error.horizon` | `no run within {years} years` | the planner found nothing inside the horizon |
| `error.count` | `count must be between 1 and {max}` | a count below 1 or above `max_count` |

## Validation

| Setting | Value | Meaning |
|---|---|---|
| `validate.result` | `list of messages` | `validate()` returns one `<field>: <problem>` string per problem, or an empty list |
| `validate.reports` | `first problem` | validation stops at the first problem it finds |

## Descriptions

| Setting | Value | Meaning |
|---|---|---|
| `describe.clock` | `24-hour` | times of day are written like `09:30` |
| `describe.exact_times` | `4` | up to this many times of day are spelled out one by one |
| `describe.steps` | `listed` | a stepped minute or hour field is described by listing its values |

## Jobs files

One job per line: a name, whitespace, then an expression. Blank lines are
skipped.

| Setting | Value | Meaning |
|---|---|---|
| `jobs.line` | `<name> <expression>` | the shape of a job line |
| `jobs.comment` | `#` | a line starting with this is ignored |
| `jobs.name` | `[A-Za-z0-9_.-]+` | characters allowed in a job name |
| `jobs.error` | `line {line}: {message}` | an invalid expression; the message is the first problem found |
| `jobs.duplicate` | `line {line}: duplicate job '{name}'` | a name used twice |
| `jobs.bad_name` | `line {line}: invalid job name '{name}'` | a name with other characters |

## Command line

| Setting | Value | Meaning |
|---|---|---|
| `cli.run_format` | `YYYY-MM-DD HH:MM Ddd` | how `next`, `last`, `between`, `upcoming` and `overlaps` print a run |
| `cli.json` | `ISO 8601 strings` | what `--json` prints for each run |
| `cli.error_prefix` | `cronish:` | errors go to standard error after this prefix |
| `cli.check_ok` | `ok` | what `check` prints for a usable expression |
| `cli.overlap_hours` | `24` | how far ahead `overlaps` looks unless `--hours` is given |
| `exit.ok` | `0` | success |
| `exit.invalid` | `1` | an invalid expression or jobs file |
| `exit.usage` | `2` | a usage error from the argument parser |
