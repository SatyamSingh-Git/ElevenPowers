# Changelog

## Unreleased

- `--profile` describes each column (number or text, filled and blank cells) instead of reporting.

## 0.9.0

- `--where` keeps only rows matching a filter such as `region=East` or `amount>=100`.
- `--sort` orders groups by any report column; a leading `-` sorts descending.
- Accounting negatives such as `(12.50)` are read as negative amounts.

## 0.8.0

- First release: grouped sum, count, mean, min and max over a CSV file, as plain or markdown tables.
