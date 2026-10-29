# surveytally

Import survey responses, check them against the questionnaire, weight them and
tabulate the results.

```
surveytally init customer survey.json
surveytally import customer responses.csv
surveytally weight customer targets.csv
surveytally summary customer
surveytally export customer tables.csv
surveytally crosstab customer satisfaction region --significance
```

A survey file describes the questionnaire: its questions (single choice,
multiple choice, scale or free text) and the scores built from them. Response
files are CSV, one column per question, or JSON lines. See
[docs/reference.md](docs/reference.md) for every default, format and message.

## Layout

- `src/surveytally/model` questions, surveys and responses
- `src/surveytally/files` survey, response, weights and targets files, and the project folder
- `src/surveytally/services` validation, cleaning, weighting, scoring, tallies and cross-tabulations
- `src/surveytally/reports` tables, exports, summaries and wave comparisons
- `src/surveytally/cli` the command line

`src/surveytally/_generated.py` is generated from the shared scale library.

## Development

```
python -m pytest
```
