# Changelog

## Unreleased

## 0.4.0

- Ledger: `summarize` and `render_ledger` add exported records up by region and currency.
- `python -m invoicekit export` writes invoices as JSON lines records.
- Fixed amount discounts add up to exactly the amount; leftover cents go to the earliest lines.

## 0.3.0

- Tax rates for India (GST).
- Rounding mode is an invoice field (`half-up`, `half-even`, `down`).

## 0.2.0

- Percent discounts can be limited to one category.
- Printed invoices show one tax row per rate.
