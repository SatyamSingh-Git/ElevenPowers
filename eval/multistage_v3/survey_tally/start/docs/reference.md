# surveytally reference

Every documented default, limit, file format detail and message. The first
column is the name we use for a fact, the second its current value, the third
what it means and which surface it belongs to: the CLI, an API call or a file.

## Command line

| Fact | Value | Meaning |
|---|---|---|
| `exit_ok` | `0` | CLI exit status of a command that succeeded |
| `exit_error` | `1` | CLI exit status when a file, folder or setting cannot be used |
| `exit_usage` | `2` | CLI exit status for a mistake in the command itself |
| `exit_invalid` | `3` | CLI exit status of `import` and `validate` when responses have problems |
| `--decimals` | `1` | CLI default decimals for percentages, unless surveytally.ini sets `decimals` |
| `--format` | `csv` | CLI default format for `export` and `crosstab --out`, unless surveytally.ini sets `format` |
| `export_formats` | `csv, markdown, text` | formats the CLI `--format` option and surveytally.ini accept |
| `json_lines_suffixes` | `.jsonl, .ndjson` | response file suffixes the CLI reads and writes as JSON lines; any other is CSV |
| `config_file` | `surveytally.ini` | settings file the CLI reads from a project folder, section `[surveytally]` |
| `min_seconds` | `0` | surveytally.ini default: CLI `import` drops responses faster than this many seconds; 0 keeps all |
| `compare_columns` | `question, option, before, after, change` | columns of the CLI `compare` output |

## Project folder

| Fact | Value | Meaning |
|---|---|---|
| `survey_file` | `survey.json` | survey file inside a project folder |
| `responses_file` | `responses.jsonl` | file of accepted responses inside a project folder, one JSON object per line |
| `weights_file` | `weights.csv` | weights file inside a project folder, written by the CLI `weight` command |

## Survey file

| Fact | Value | Meaning |
|---|---|---|
| `schema` | `2` | newest survey file schema this release reads, and the one it writes |
| `question_types` | `single, multi, scale, text` | values of a question's `type` in a survey file |
| `scale_low` | `1` | lowest point of a scale question in a survey file that sets neither `low` nor `preset` |
| `scale_high` | `5` | highest point of a scale question in a survey file that sets neither `high` nor `preset` |
| `scale_presets` | `agree5, satisfied5, frequency5, quality4, likely11` | names a scale question's `preset` may take in a survey file |
| `text_max_length` | `500` | longest answer accepted for a `text` question in a survey file that sets no `max_length` |
| `score_rules` | `sum, mean, top_box, nps` | names a score's `rule` may take in a survey file |

## Response files

| Fact | Value | Meaning |
|---|---|---|
| `respondent_column` | `respondent` | required column of a response CSV file holding the respondent id |
| `submitted_column` | `submitted` | optional column of a response CSV file holding the date, YYYY-MM-DD |
| `duration_column` | `duration` | optional column of a response CSV file holding the whole seconds taken |
| `missing_values` | `NA` | cell that, like an empty cell, means no answer in a response CSV file |
| `multi_separator` | `;` | separator between the options picked in a multiple-choice cell of a response CSV file |
| `respondent_case` | `as given` | how respondent ids read from response files (CSV or JSON lines) are kept |
| `encoding` | `utf-8` | encoding of response CSV files; a byte order mark is allowed |

## Weights and targets files

| Fact | Value | Meaning |
|---|---|---|
| `weight_columns` | `respondent, weight` | columns of a weights file |
| `weight_decimals` | `6` | decimals of each weight in a weights file the CLI writes |
| `target_columns` | `question, option, share` | columns of a targets file |
| `share_tolerance` | `0.001` | how far a question's shares in a targets file may be from adding up to 1 |

## Weighting

| Fact | Value | Meaning |
|---|---|---|
| `weight_cap` | `5.0` | largest weight `compute_weights` (API) and the CLI `weight` command keep after trimming |
| `weight_floor` | `0.2` | smallest weight `compute_weights` (API) keeps after trimming |
| `max_iterations` | `50` | most raking passes `compute_weights` (API) makes |

## Tables and exports

| Fact | Value | Meaning |
|---|---|---|
| `frequency_columns` | `question, option, count, percent` | columns of frequency tables in a CSV file from `export_frequencies` (API) or the CLI `export` |
| `frequency_order` | `count` | order of choice options in frequency tables from `frequencies` (API) and in exported files; `count` puts the most chosen first |
| `missing_label` | `(no answer)` | label of the row counting respondents without an answer, in exported table files |
| `total_label` | `Total` | heading of a cross-tabulation's total column, in exported table files |
| `base_label` | `n` | label of a cross-tabulation's row of column bases, in exported table files |
| `percent_rounding` | `half-even` | how percentages in exported table files round: a half goes to the even digit |
| `mean_decimals` | `2` | decimals of scale means and mean scores in exported and printed tables |
| `codebook_columns` | `question, type, code, label` | columns of a codebook CSV file |

## Scoring

| Fact | Value | Meaning |
|---|---|---|
| `top_box_points` | `2` | top points of a scale the `top_box` rule counts (API `compute_scores`) |
| `nps_promoter` | `9` | lowest answer the `nps` rule counts as a promoter (API `compute_scores`) |
| `nps_detractor` | `6` | highest answer the `nps` rule counts as a detractor (API `compute_scores`) |

## Quality checks and significance

| Fact | Value | Meaning |
|---|---|---|
| `straightline_items` | `4` | scale questions answered alike before the CLI `quality` command flags a straightliner |
| `max_skipped_share` | `0.5` | share of questions skipped above which the CLI `quality` command flags a respondent |
| `significance_z` | `1.96` | z score a difference must exceed to earn a letter with the CLI `--significance` option |
| `significance_min_base` | `30` | smallest unweighted column base the CLI `--significance` option compares |

## Messages

| Fact | Value | Meaning |
|---|---|---|
| `error.unknown_option` | `{question}: unknown option {code}` | problem reported by `validate` (API) and the CLI `import` and `validate` |
| `error.out_of_range` | `{question}: {value} is outside {low}..{high}` | problem reported by `validate` (API) and the CLI `import` and `validate` |
| `error.too_long` | `{question}: answer longer than {limit} characters` | problem reported by `validate` (API) and the CLI `import` and `validate` |
| `error.required` | `{question}: answer required` | problem reported by `validate` (API) and the CLI `import` and `validate` |
| `error.too_many` | `{question}: more than {limit} options chosen` | problem reported by `validate` (API) and the CLI `import` and `validate` |
| `error.unknown_column` | `row 1: unknown question column {column}` | error reading a response CSV file |
| `error.not_whole_number` | `row {row}: {question} expects a whole number, got {value}` | error reading a response CSV file |
| `error.unknown_type` | `{file}: question {question} has unknown type {type}` | error loading a survey file |
| `error.unknown_rule` | `unknown scoring rule {rule}` | error from `compute_scores` (API) and problem listed by the CLI `check` |
| `error.no_weight` | `no weight for respondent {respondent}` | error when weights lack a respondent being analysed (API and CLI) |
