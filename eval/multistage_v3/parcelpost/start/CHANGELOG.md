# Changelog

## Unreleased

- `parcelpost settings` prints the settings in effect.

## 1.4.0 - 2026-09-30

- Saved recipients: `parcelpost address add` and `parcelpost book --recipient`.
- Shipper notifications are queued in `outbox.jsonl` for registered accounts.
- `parcelpost report zones` shows shipments and revenue by zone.

## 1.3.0 - 2026-08-12

- Claims for lost and damaged parcels.
- `parcelpost archive` and `parcelpost check`.
- ZPL labels with `label_format = zpl`.

## 1.2.0 - 2026-06-03

- Customer accounts with payment terms; invoices show the due date.
- Reconciliation against the carrier's invoice.
