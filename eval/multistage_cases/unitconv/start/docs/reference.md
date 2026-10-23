# unitconv reference

`unitconv` converts quantities such as `12.5 km/h` between units. The library
lives in `src/unitconv`; the command line is `python -m unitconv`.

## Settings

Settings come from defaults, then a settings file (`--settings FILE`), then
command-line options, each overriding the one before.

| Setting | Value | Meaning |
|---|---|---|
| `precision` | `6` | default number of decimal places in results |
| `precision.max` | `15` | largest precision accepted |
| `rounding` | `half_even` | default rounding mode |
| `rounding.modes` | `half_even, half_up, half_down, up, down, ceiling, floor` | accepted rounding modes |
| `style` | `symbol` | default way to write units in results |
| `style.values` | `symbol, name` | `symbol` writes `km`, `name` writes `kilometres` |
| `settings.format` | `key = value` | one setting per line of a settings file |
| `settings.comment` | `#` | starts a comment that runs to the end of the line |

## Conversion

| Fact | Value | Meaning |
|---|---|---|
| `convert.result` | `rounded` | `convert()` returns its value rounded to `precision` places with the `rounding` mode |
| `arithmetic` | `float` | numbers are binary floating point while converting |
| `lookup.case` | `insensitive` | unit symbols match regardless of case when there is no exact match |
| `prefixes` | `G, M, k, h, da, d, c, m, u, n` | SI prefixes accepted before units that take them |
| `table.version` | `2026.3` | version of the generated unit table |
| `temperature.offsets` | `degC, degF` | units with an offset; they cannot be part of a compound unit |

## Writing units

Compound units multiply and divide named units. Each `/` divides by the single
term that follows it, so `W/m^2/K` is watts per square metre per kelvin.

| Fact | Value | Meaning |
|---|---|---|
| `unit.multiply` | `*` | joins units that multiply, as in `kg*m` |
| `unit.divide` | `/` | divides by the next unit, as in `m/s` |
| `unit.power` | `^n` | raises a unit to an integer power, as in `s^2` or `s^-2` |
| `unit.reciprocal` | `1/` | a unit with nothing above the line, as in `1/s` |
| `output.round_trip` | `yes` | every quantity unitconv prints is accepted back as input |
| `mixed.separator` | `+` | a target such as `ft+in` gives whole feet and the remaining inches |

## Errors

| Error | Message | When |
|---|---|---|
| `error.unknown_unit` | `unknown unit: '{unit}'` | a symbol names no unit |
| `error.incompatible` | `cannot convert {source} ({source_dimension}) to {target} ({target_dimension})` | the dimensions differ |
| `error.parse_quantity` | `cannot parse quantity: '{text}'` | the text is not a number followed by a unit |
| `error.parse_unit` | `cannot parse unit: '{text}'` | a unit expression is malformed or cancels out |
| `error.offset` | `offset unit '{unit}' cannot be combined` | an offset unit inside a compound or mixed unit |
| `error.precision` | `precision must be between 0 and {max}` | precision outside the accepted range |
| `error.rounding` | `unknown rounding mode: '{mode}'` | a rounding mode not listed above |
| `error.style` | `unknown style: '{style}'` | a style not listed above |
| `error.dimension` | `unknown dimension: '{name}'` | `list --dimension` with an unknown name |
| `error.setting` | `unknown setting: '{key}'` | a settings file names an unknown setting |
| `error.settings_line` | `line {n}: expected 'key = value'` | a settings file line without `=` |
| `error.mixed_units` | `a mixed result needs at least two units` | a mixed target with one unit |
| `error.mixed_negative` | `a mixed result needs a quantity of zero or more` | a negative quantity with a mixed target |
| `error.mixed_json` | `JSON output needs a single target unit` | `--json` with a mixed target |
| `error.batch_columns` | `expected 2 columns, got {count}` | a batch row without exactly two cells |

## Command line

`unitconv convert QUANTITY TARGET`, `unitconv list [--dimension NAME]`,
`unitconv dimensions`, `unitconv info UNIT` and `unitconv batch SOURCE DESTINATION`.
`convert` and `batch` take `--precision`, `--rounding`, `--style` and `--settings`.

| Fact | Value | Meaning |
|---|---|---|
| `exit.ok` | `0` | success |
| `exit.error` | `1` | a conversion or settings error, or a batch with failed rows |
| `exit.usage` | `2` | the command line itself is wrong |
| `cli.error` | `error: {message}` | how errors are written to standard error |
| `batch.summary` | `converted {converted} rows, {failed} failed` | printed after a batch |

Command-line options that are not settings, with their defaults:

| Option | Default | Meaning |
|---|---|---|
| `--json` | `off` | `convert` only: print a JSON object instead of text |
| `--dimension` | `all` | `list` only: show only the units of one named dimension |

## JSON output

`unitconv convert ... --json` prints one object.

| Field | Value | Meaning |
|---|---|---|
| `json.fields` | `input, value, unit, text` | keys of the object |
| `json.input` | `string` | the quantity as given |
| `json.value` | `number` | the converted value, rounded as in `text` |
| `json.unit` | `string` | the target unit's symbol |
| `json.text` | `string` | the result as `convert` prints it |

## Batch files

The source is CSV with a quantity and a target unit per row. Blank rows and
rows starting with `#` are skipped.

| Field | Value | Meaning |
|---|---|---|
| `batch.columns` | `input, target, value, unit, error` | header and columns of the result file |
| `batch.encoding` | `utf-8` | encoding of both files |
