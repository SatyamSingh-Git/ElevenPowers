# stockroom reference

## Command-line options

| Option | Default | Meaning |
|---|---|---|
| `--file` | `stockroom.json` | data file; `STOCKROOM_FILE` overrides the default |
| `--unit` | `ea` | unit of measure for `add-item` |
| `--reorder` | `0` | reorder point for `add-item`; 0 never reports the item as low |
| `--cost` | `0.00` | unit cost for `add-item`, in dollars and cents |
| `--kind` | `shelf` | kind of location for `add-location` |
| `--description` | `` | free text for `add-location` |
| `--note` | `` | free text stored on a movement |

## Data file

One JSON document. Item SKUs and location codes are stored upper-case.

| Field | Type | Meaning |
|---|---|---|
| `version` | `1` | schema version of the data file |
| `items.<sku>.name` | `string` | item name |
| `items.<sku>.unit` | `string` | unit of measure |
| `items.<sku>.reorder_point` | `integer` | the item is low when its total on hand is below this |
| `items.<sku>.unit_cost` | `string` | unit cost in dollars with two decimal places, e.g. "2.50" |
| `locations.<code>.kind` | `string` | one of the location kinds |
| `locations.<code>.description` | `string` | free text |
| `stock.<sku>.<code>` | `integer` | quantity held; locations holding none are left out |
| `movements[].seq` | `integer` | 1 for the first movement, then one higher for each |
| `movements[].type` | `string` | `receive`, `issue`, `transfer` or `adjust` |
| `movements[].sku` | `string` | item moved |
| `movements[].qty` | `integer` | quantity moved; for `adjust`, the signed change |
| `movements[].from` | `string or null` | location the goods left; null for `receive` and `adjust` |
| `movements[].to` | `string or null` | location the goods reached; null for `issue` |
| `movements[].note` | `string` | free text |

## Limits

| Limit | Value | Meaning |
|---|---|---|
| `sku length` | `1-24` | letters, digits and `-`, starting with a letter or digit |
| `location code length` | `1-12` | letters, digits and `-`, starting with a letter or digit |
| `item name length` | `1-80` | characters after trimming |
| `max quantity` | `1000000` | largest quantity, count or reorder point |
| `low-stock rule` | `on hand < reorder point` | total across all locations; a reorder point of 0 never fires |

## Library

| Call | Returns | Meaning |
|---|---|---|
| `Inventory.on_hand(sku)` | `int` | total quantity across every location |
| `Inventory.at(sku, location)` | `int` | quantity held at one location; 0 when none is held there |
| `Inventory.receive(sku, qty, location)` | `quantity` | quantity now held at the location |
| `Inventory.issue(sku, qty, location)` | `quantity` | quantity left at the location |
| `Inventory.transfer(sku, qty, source, dest)` | `quantity` | quantity now held at the destination |
| `Inventory.adjust(sku, location, counted)` | `change` | counted minus what was recorded |

## Errors

Every refusal raises `StockError`; the command prints `error: <message>` and exits 1.

| Error | Message | Meaning |
|---|---|---|
| `unknown item` | `unknown item: <sku>` | |
| `unknown location` | `unknown location: <code>` | |
| `duplicate item` | `item already exists: <sku>` | |
| `duplicate location` | `location already exists: <code>` | |
| `insufficient stock` | `insufficient stock: <sku> at <code> has <held>, needs <qty>` | issue or transfer of more than is held |
| `bad quantity` | `quantity must be a whole number from 1 to 1000000: <text>` | |
| `bad count` | `count must be a whole number from 0 to 1000000: <text>` | |
| `bad cost` | `cost must be dollars and cents, like 2.50: <text>` | |
| `unsupported version` | `unsupported data file version: <version>` | |
| `exit status` | `1` | for any refusal; `check` also exits 1 on a mismatch |
