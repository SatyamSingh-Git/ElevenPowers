# tabreport reference

The facts below are what the code does. Each table row is one fact: the key,
its value, and what it means.

## Reading CSV

| Key | Value | Meaning |
|---|---|---|
| `delimiter` | `,` | field separator, exactly one character |
| `quotechar` | `"` | quote character, exactly one character, different from the delimiter |
| `encoding` | `utf-8` | text encoding of the input file |
| `skip_blank` | `true` | blank lines are ignored; when false they become rows of empty cells |
| `dialects` | `comma, semicolon, tab, pipe` | named presets for `--dialect`; `--delimiter`, `--quotechar` and `--encoding` override them |
| `default dialect` | `comma` | used when `--dialect` is not given |
| `read_csv returns` | `list of dicts` | one dict per data row, keyed by the stripped header names, cells stripped |
| `header` | `first non-blank line` | column names must be non-empty and unique |

## Amounts

| Key | Value | Meaning |
|---|---|---|
| `thousands separator` | `,` | removed from amounts before parsing |
| `negative amounts` | `-12.50 or (12.50)` | a leading minus or accounting parentheses |
| `currency symbols in cells` | `ignored` | a leading symbol from the currency table, such as `$` or `CHF`, is skipped |
| `blank cells` | `skipped` | sum, mean, min and max ignore them; count still counts the row |

## Measures

| Key | Value | Meaning |
|---|---|---|
| `measures` | `sum, count, mean, min, max` | functions accepted by `--measure` |
| `measure spec` | `func:column` | `count` takes no column |
| `default measure` | `count` | used when no `--measure` is given |
| `measure label` | `func(column)` | header of a measure column; `count` is labelled `count` |
| `empty result` | `blank cell` | mean, min or max of a group with no filled cells |

## Grouping and totals

| Key | Value | Meaning |
|---|---|---|
| `group column` | `group` | header of the single key column |
| `key separator` | ` / ` | joins the values of a multi-column key |
| `group order` | `key, ascending` | order of report rows unless `--sort` is given |
| `sort descending prefix` | `-` | `--sort=-sum(amount)` puts the largest first; empty results go last |
| `totals label` | `TOTAL` | first cell of the totals row |
| `totals` | `on` | `--no-totals` leaves the row out |
| `mean total` | `mean of all rows` | not the mean of the group means |
| `min and max total` | `over all rows` | smallest and largest single value |

## Formatting

| Key | Value | Meaning |
|---|---|---|
| `currency` | `USD` | every measure except count is money in this currency |
| `currency none` | `plain numbers` | `--currency none` prints measures without a symbol |
| `currencies` | `AUD, CAD, CHF, CNY, EUR, GBP, INR, JPY, KWD, NZD, SEK, USD` | codes in the generated currency table, case-insensitive |
| `money decimals` | `minor units of the currency` | 2 for USD, 0 for JPY, 3 for KWD |
| `negative money` | `-$1.00` | the sign goes before the symbol |
| `rounding` | `half up` | 2.345 prints as 2.35 |
| `format_number places` | `2` | default decimals for plain numbers |
| `format_number thousands` | `,` | default grouping separator for plain numbers |
| `format_money thousands` | `,` | grouping separator for money |
| `count format` | `whole number` | counts never show decimals |

## Output

| Key | Value | Meaning |
|---|---|---|
| `formats` | `plain, markdown` | accepted by `--format` |
| `default format` | `plain` | used when `--format` is not given |
| `plain column gap` | `2 spaces` | between columns in plain output |
| `render_table align` | `right for numeric columns` | when no `align` is given, a column whose filled cells all look like numbers or money is right-aligned, any other column left-aligned |
| `markdown pipe escape` | `\|` | a pipe inside a cell is escaped |
| `footer` | `N rows` | after a blank line: the number of input rows read, `1 row` for one |
| `profile columns` | `column, kind, filled, blank` | `--profile` output; kind is `number` or `text` |

## Command line

| Key | Value | Meaning |
|---|---|---|
| `exit ok` | `0` | report written |
| `exit error` | `2` | bad input or options |
| `error prefix` | `tabreport: error: ` | written to standard error before the message |
| `filter operators` | `= != > >= < <=` | `--where`; the four comparisons parse both sides as amounts and never match a blank cell |

## Errors

| Key | Value | Meaning |
|---|---|---|
| `error: not a number` | `not a number: '{text}'` | a cell or filter value is not an amount |
| `error: missing column` | `missing column: {name}` | a column named by an option is not in the header |
| `error: field count` | `line {n}: expected {k} fields, got {m}` | a row has the wrong number of cells |
| `error: empty input` | `empty input: no header row` | the file has no non-blank line |
| `error: duplicate column` | `duplicate column: {name}` | the header repeats a name |
| `error: decode` | `cannot decode {path} as {encoding}` | the file is not in the given encoding |
| `error: unknown measure` | `unknown measure: {func}` | not one of the measures |
| `error: unknown currency` | `unknown currency: {code}` | not in the currency table |
| `error: unknown format` | `unknown format: {name}` | `render_table` was given another format |
| `error: unknown dialect` | `unknown dialect: {name}` | not one of the dialects |
| `error: bad filter` | `bad filter: '{text}'` | no operator in a `--where` |
| `error: align` | `align needs 'l' or 'r' for each of {n} columns` | `render_table` was given a bad `align` |
| `error: sort` | `unknown sort column: {name}` | `--sort` names no column of the report |
