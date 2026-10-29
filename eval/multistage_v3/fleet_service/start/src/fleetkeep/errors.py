"""Every error fleetkeep reports, by code.

Codes are grouped by area: E10x vehicles and odometers, E11x fuel, E12x work
orders and services, E13x parts stock, E14x values typed by people, E15x fleet
files and settings, E16x defects, E17x tyres.
"""

MESSAGES = {
    "E101": "invalid vehicle id: {vehicle}",
    "E102": "unknown vehicle class: {vehicle_class}",
    "E103": "unknown vehicle: {vehicle}",
    "E104": "vehicle already exists: {vehicle}",
    "E105": "odometer went backwards for {vehicle}: {value} is below {previous}",
    "E106": "odometer jump too large for {vehicle}: {miles} miles in {days} days",
    "E107": "reading for {vehicle} on {day} is before its latest reading on {latest}",
    "E108": "model year {year} is outside {earliest}-{latest}",
    "E109": "vehicle {vehicle} cannot retire before it entered service on {in_service}",
    "E111": "fill-up must be more than zero gallons: {gallons}",
    "E112": "fill-up of {gallons} gallons is over the limit of {limit}",
    "E113": "fuel card {card} is not assigned to a vehicle",
    "E121": "unknown work order: {order}",
    "E122": "cannot change closed work order {order}",
    "E123": "work order {order} cannot close before it opened on {opened}",
    "E124": "service {code} does not apply to {vehicle_class} vehicles",
    "E125": "only an open work order with no charges can be cancelled: {order}",
    "E131": "not enough {number} in stock: {on_hand} on hand",
    "E132": "no price given for unstocked part {number}",
    "E133": "part {number} is not stocked",
    "E141": "invalid amount: {text}",
    "E142": "invalid date: {text}",
    "E143": "invalid number: {text}",
    "E144": "period ends before it starts: {start} to {end}",
    "E145": "{path} is missing columns: {columns}",
    "E146": "no reading for {vehicle} on {day}",
    "E151": "unknown setting in fleet.ini: {name}",
    "E152": "invalid value for {name}: {value}",
    "E153": "no fleet in {path}",
    "E154": "a fleet already exists in {path}",
    "E161": "unknown defect: {defect}",
    "E162": "unknown defect severity: {severity}",
    "E163": "defect {defect} is already fixed",
    "E164": "defect {defect} is not on {vehicle}",
    "E171": "tyre position must be one of {positions}: {position}",
    "E172": "tread depth must be 0-32 (32nds of an inch): {depth}",
}


class FleetError(Exception):
    """A problem with the fleet's data or with what someone asked for."""

    def __init__(self, code, /, **fields):
        self.code = code
        self.fields = fields
        super().__init__(f"{code} {MESSAGES[code].format(**fields)}")
