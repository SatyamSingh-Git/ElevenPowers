# parcelpost reference

The facts below are what the code does today. Each table lists the key, its
value and where it applies.

## Settings

Read from `parcelpost.ini` in the data directory, section `[parcelpost]`. A
missing file or section means every default applies.

| key | default | meaning |
|---|---|---|
| `fuel_percent` | `7.5` | settings file: fuel levy, as a percent of base postage plus surcharges |
| `vat_percent` | `20` | settings file: VAT percent added to invoices and statements |
| `stale_hours` | `48` | settings file: hours without a scan before an undelivered shipment is reported stalled |
| `cutoff` | `17:00` | settings file: bookings at or after this time ship the next business day |
| `default_service` | `ground` | settings file: service used when a booking names none |
| `depot` | `BHX` | settings file: depot code on collection requests |
| `label_format` | `text` | settings file: `text` or `zpl` |
| `unknown setting` | `unknown setting: {key}` | settings file: error for a key not listed here |
| `invalid setting` | `invalid value for {key}: {value}` | settings file: error for a value that does not parse |

## Command line

| option or output | value | meaning |
|---|---|---|
| `--data-dir` | `.parcelpost` | CLI: directory holding shipments, events, manifests, labels and invoices |
| `--size` | `20x15x10` | CLI `quote` and `book`: parcel size in centimetres when not given |
| `--value` | `0.00` | CLI `quote` and `book`: declared value in pounds when not given |
| `exit: error` | `1` | CLI: exit status when a command fails |
| `exit: usage` | `2` | CLI: exit status for a command line that does not parse |
| `exit: not found` | `3` | CLI: exit status when a tracking number is not in the store |
| `error output` | `error: {message}` | CLI: how a failure is printed on standard error |
| `book output` | `booked {number} {service} {total}` | CLI `book`: first line printed |
| `scan output` | `recorded {scans} scans for {shipments} shipments` | CLI `scan`: line printed |

## Limits

| limit | value | meaning |
|---|---|---|
| `max weight` | `30 kg` | heaviest parcel accepted |
| `max side` | `150 cm` | longest side accepted |
| `max declared value` | `2500.00` | highest declared value accepted, in pounds |
| `volumetric divisor` | `5000` | cubic centimetres per kilogram of volumetric weight |
| `weight step` | `0.5 kg` | billable weight is rounded up to a multiple of this |
| `address field length` | `35` | most characters in a recipient's name, first line or town |
| `return window` | `30` | days after the expected delivery date that a return can be booked |
| `standard cover` | `20.00` | most a claim pays, in pounds, for a parcel without insurance |
| `payment days` | `30` | days an invoice gives an account that has no terms of its own |

## Surcharges

Applied in this order, after base postage. The fuel levy is then charged on
the total of base postage and surcharges.

| surcharge | amount | meaning |
|---|---|---|
| `residential` | `3.50` | delivery to a home address |
| `signature` | `2.00` | signature required on delivery |
| `oversize` | `12.00` | parcels over 25 kg, or with a side longer than 100 cm |
| `insurance` | `1.5%` | of the declared value, at least 2.00, when the declared value is over 100.00 |

## Errors

| error | message | meaning |
|---|---|---|
| `too heavy` | `parcel too heavy: {weight} kg (max 30 kg)` | a parcel over the weight limit |
| `too long` | `parcel too long: {length} cm (max 150 cm)` | a parcel with a side over the limit |
| `declared value too high` | `declared value {value} is over the limit of {limit}` | a declared value over the limit |
| `invalid postcode` | `invalid postcode: {postcode}` | a postcode that is not UK style |
| `no zone` | `no service to postcode area {area}` | a postcode area outside the zone chart |
| `unknown service` | `unknown service: {service}` | a service not on the rate card |
| `invalid account` | `invalid account: {account} (2 to 10 capital letters or digits)` | an account code that does not fit |
| `unknown shipment` | `no shipment {number}` | a tracking number not in the store |
| `nothing to manifest` | `no shipments to manifest for {day}` | closing a day with nothing booked to ship on it |
| `day closed` | `manifest for {day} is already closed` | closing a day twice |
| `no manifest` | `no manifest for {day}; close the day first` | billing or reconciling a day that is not closed |
| `bad tracking number` | `line {line}: invalid tracking number {number}` | scan file: a number with the wrong layout or check digit |
| `unknown scan code` | `line {line}: unknown scan code {code}` | scan file: a code not listed under scan codes |
| `scan for unknown shipment` | `line {line}: no shipment {number}` | scan file: a valid number that was never booked |

## Scan codes

The carrier's scan file sets each scanned shipment to the status of its latest
scan.

| code | status | meaning |
|---|---|---|
| `PU` | `in_transit` | collected from the depot |
| `AR` | `in_transit` | arrived at a hub |
| `DP` | `in_transit` | left a hub |
| `OFD` | `in_transit` | on the van for delivery today |
| `DL` | `delivered` | delivered |
| `EX` | `exception` | delivery problem |
| `RT` | `returned` | on its way back to the depot |

## Tracking numbers

| fact | value | meaning |
|---|---|---|
| `tracking number` | `PP{serial}{check}GB` | eight-digit serial from the booking sequence, then one check digit |
| `check digit` | `mod 10, weights 3 1` | how the check digit is computed from the eight serial digits |

## Files

All paths are relative to the data directory.

| file | path | meaning |
|---|---|---|
| `store file` | `shipments.json` | every shipment, with the next sequence number |
| `events file` | `events.jsonl` | one tracking event per line: `number`, `code`, `at`, `depot` |
| `manifest file` | `manifests/manifest-{day}.csv` | the carrier manifest for one collection day |
| `label file` | `labels/{number}.txt` | the label for a shipment; `.zpl` when `label_format` is `zpl` |
| `invoice number` | `INV-{account}-{yyyymmdd}` | invoice file name, under `invoices/`, without `.txt` |

## Manifest file

| column or rule | value | meaning |
|---|---|---|
| `manifest columns` | `tracking_number,account,service,zone,weight_g,billable_g,charge,surcharges` | manifest file: header row |
| `charge` | `1250` | manifest file: the shipment's total charge, in whole pence |
| `surcharges` | `joined with +` | manifest file: surcharge codes on the shipment's quote |
| `manifest order` | `account, tracking number` | manifest file: order of the shipment lines |
