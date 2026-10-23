# invoicekit reference

Amounts are decimals. Pass them as strings or integers; floats are refused
because they cannot hold most cent values exactly.

## Invoice fields

`invoice_from_dict` reads a dict with these keys. The second column is
`required`, `optional`, or the value used when the key is absent.

| Field | Default | Meaning |
|---|---|---|
| `number` | `required` | Invoice number, printed in the heading. |
| `issued` | `optional` | Issue date, `YYYY-MM-DD`. |
| `region` | `required` | Tax region code, case-insensitive. See the tax rates below. |
| `currency` | `USD` | ISO 4217 code. |
| `rounding` | `half-up` | Rounding mode for every amount on the invoice. |
| `lines` | `required` | Line items, at least one and at most 200. |
| `discounts` | `optional` | Discounts, applied in the order given. |

## Line item fields

| Field | Default | Meaning |
|---|---|---|
| `line.sku` | `required` | Stock keeping unit, must not be empty. |
| `line.description` | `required` | At most 120 characters. |
| `line.quantity` | `required` | Number of units, from 1 to 10000. |
| `line.unit_price` | `required` | Price of one unit, not negative. |
| `line.category` | `standard` | One of `standard`, `food`, `books`, `digital`, `services`. |

## Discount fields

| Field | Default | Meaning |
|---|---|---|
| `discount.kind` | `required` | `percent` or `amount`. |
| `discount.percent` | `required` | For `percent`: from 0 to 100, taken off each line it covers. |
| `discount.category` | `optional` | For `percent`: only lines of this category; all lines when absent. |
| `discount.amount` | `required` | For `amount`: taken off the invoice, spread over the lines in proportion to what is left of each. |

Percent discounts apply first, then fixed amounts. A fixed amount larger than
what is left is capped there; no line goes below zero. The shares of a fixed
amount add up to exactly that amount, any leftover minor unit going to the
earliest lines.

## Rounding modes

| Mode | Python constant | Meaning |
|---|---|---|
| `half-up` | `ROUND_HALF_UP` | 2.345 becomes 2.35. |
| `half-even` | `ROUND_HALF_EVEN` | 2.345 becomes 2.34. |
| `down` | `ROUND_DOWN` | Towards zero. |

Line amounts, each line's discount and each line's tax are rounded to the
currency's minor units. Invoice totals are sums of the rounded line values.

## Currencies

Read from `src/invoicekit/_generated.py`. The value is the number of minor units.

| Code | Minor units | Printed as |
|---|---|---|
| `CHF` | `2` | CHF 1,234.50 |
| `EUR` | `2` | €1,234.50 |
| `GBP` | `2` | £1,234.50 |
| `INR` | `2` | ₹1,234.50 |
| `JPY` | `0` | ¥1,235 |
| `KWD` | `3` | KD 1,234.500 |
| `USD` | `2` | $1,234.50 |

Negative amounts are printed with a minus sign before the symbol: `-$12.00`.

## Tax rates

Keyed `rate.<region>.<category>.<date the rate took effect>`. Tax is charged on
each line's amount after discounts.

| Rate | Percent | Note |
|---|---|---|
| `rate.US-NY.standard.2009-08-01` | `8.875%` | New York City combined rate. |
| `rate.US-NY.food.2009-08-01` | `0%` | |
| `rate.US-NY.books.2009-08-01` | `8.875%` | |
| `rate.US-NY.digital.2009-08-01` | `8.875%` | |
| `rate.US-NY.services.2009-08-01` | `0%` | |
| `rate.DE.standard.2021-01-01` | `19%` | |
| `rate.DE.food.2021-01-01` | `7%` | Reduced rate. |
| `rate.DE.books.2021-01-01` | `7%` | Reduced rate. |
| `rate.DE.digital.2021-01-01` | `19%` | |
| `rate.DE.services.2021-01-01` | `19%` | |
| `rate.GB.standard.2011-01-04` | `20%` | |
| `rate.GB.food.2011-01-04` | `20%` | |
| `rate.GB.books.2011-01-04` | `20%` | |
| `rate.GB.digital.2011-01-04` | `20%` | |
| `rate.GB.services.2011-01-04` | `20%` | |
| `rate.JP.standard.2019-10-01` | `10%` | |
| `rate.JP.food.2019-10-01` | `8%` | Reduced rate. |
| `rate.JP.books.2019-10-01` | `10%` | |
| `rate.JP.digital.2019-10-01` | `10%` | |
| `rate.JP.services.2019-10-01` | `10%` | |
| `rate.IN.standard.2017-07-01` | `18%` | GST. |
| `rate.IN.food.2017-07-01` | `5%` | |
| `rate.IN.books.2017-07-01` | `0%` | |
| `rate.IN.digital.2017-07-01` | `18%` | |
| `rate.IN.services.2017-07-01` | `18%` | |

## Printed invoice

`render_text(invoice, width=64)` returns the invoice as plain text: a heading,
one row per line item (with its discount underneath when it has one), then
subtotal, discount, one tax row per rate and the total.

| Option | Default | Meaning |
|---|---|---|
| `width` | `64` | Characters per row, at least 56. |

## Exported records

`to_record(invoice)` returns a dict ready for JSON; `write_records` and
`read_records` store a list of them as JSON lines. Each record carries its
lines as well, with their own amounts and the rate charged.

| Field | JSON type | Meaning |
|---|---|---|
| `record.number` | `string` | Invoice number. |
| `record.region` | `string` | Normalised region code. |
| `record.currency` | `string` | ISO 4217 code. |
| `record.subtotal` | `string` | Sum of line amounts before discounts, as a decimal. |
| `record.discount` | `string` | Total discount, as a decimal. |
| `record.tax` | `string` | Total tax, as a decimal. |
| `record.total` | `string` | Amount due, as a decimal. |
| `record.lines` | `array` | One object per line item. |

## Ledger

`summarize(records)` adds exported records up by region and currency and
returns one `LedgerRow` per pair (`region`, `currency`, `invoices`,
`subtotal`, `discount`, `tax`, `total`), sorted by region then currency.
`render_ledger(rows)` prints them as a table, discounts as negative amounts.

## Errors

Every error is a `ValueError`; the class names the stage that refused the input.
Line item errors are prefixed with the line number, as in `line 2: unknown category: toys`.

| Message | Class | Raised when |
|---|---|---|
| `invoice missing field: {name}` | `InvoiceError` | A required invoice field is absent. |
| `issue date must be YYYY-MM-DD, not {value}` | `InvoiceError` | The issue date does not parse. |
| `an invoice needs at least one line item` | `InvoiceError` | |
| `an invoice may have at most 200 line items` | `InvoiceError` | |
| `unknown rounding mode: {name}` | `InvoiceError` | |
| `line item missing field: {name}` | `ItemError` | |
| `quantity must be a whole number` | `ItemError` | The quantity is not an integer. |
| `quantity must be between 1 and 10000` | `ItemError` | |
| `unit price must not be negative` | `ItemError` | |
| `unknown category: {name}` | `ItemError` | |
| `description must be at most 120 characters` | `ItemError` | |
| `discount percent must be between 0 and 100` | `DiscountError` | |
| `discount amount must not be negative` | `DiscountError` | |
| `unknown discount kind: {kind}` | `DiscountError` | |
| `unknown region: {code}` | `TaxError` | |
| `unknown currency: {code}` | `MoneyError` | |
| `amounts must be strings or integers, not float` | `MoneyError` | |
| `width must be at least 56` | `ValueError` | `render_text` was given a narrower width. |
