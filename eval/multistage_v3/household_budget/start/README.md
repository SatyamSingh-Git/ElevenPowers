# budgetbook

Household budgeting in plain files. A budget folder holds the transactions as
CSV and everything else as small JSON files, so it can live in a synced folder
and be read by other tools.

```
budgetbook --dir ~/budget init --currency GBP
budgetbook --dir ~/budget account add Current --opening 1250.00
budgetbook --dir ~/budget import Current ~/Downloads/statement.csv
budgetbook --dir ~/budget budget status 2026-03
budgetbook --dir ~/budget close 2026-03
budgetbook --dir ~/budget report month 2026-03
```

See `docs/reference.md` for file formats, defaults and messages.

## Development

```
pip install -e . pytest
pytest
```
