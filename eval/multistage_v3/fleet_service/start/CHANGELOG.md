# Changelog

## Unreleased

- Parts stock: `parts receive`, `parts count` and `parts stock`; a stocked part is charged at its average cost.
- `fleetkeep check` lists stale work orders, vehicles missing odometer readings, worn tyres and grounded vehicles.
- `odometer fix` corrects a mistyped reading.
- `fleetkeep summary` puts each vehicle's miles, costs, economy and shop days on one line.

## 0.3.0

- Inspection defects and tyre tread readings.
- Fuel cards: a fuel-card row with no unit is charged to the card's vehicle.
- Work orders can be opened for a breakdown; `downtime` reports breakdown days separately.

## 0.2.0

- Telematics, timesheet, service history and delivery schedule imports.
- `fleetkeep spend` and `fleetkeep downtime`.
