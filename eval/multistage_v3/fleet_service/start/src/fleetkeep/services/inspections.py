"""Recording inspection findings and tying defects to the work orders that fix them."""
from ..errors import FleetError
from ..model.inspection import Defect, TreadReading


def _next_id(fleet):
    numbers = [int(defect.id.removeprefix("D-")) for defect in fleet.defects()]
    return f"D-{max(numbers, default=0) + 1:04d}"


def report_defect(fleet, vehicle_id, day, description, severity="minor"):
    vehicle = fleet.vehicle(vehicle_id)
    defect = Defect(_next_id(fleet), vehicle.id, day, description.strip(), severity)
    fleet.add_defect(defect)
    return defect


def assign_defects(fleet, order, defect_ids):
    """Put open defects of the order's vehicle on the order; closing it fixes them."""
    for defect_id in defect_ids:
        defect = fleet.defect(defect_id)
        if defect.vehicle_id != order.vehicle_id:
            raise FleetError("E164", defect=defect.id, vehicle=order.vehicle_id)
        if not defect.is_open:
            raise FleetError("E163", defect=defect.id)
    for defect_id in defect_ids:
        fleet.defect(defect_id).order_id = order.id


def fix_defects(fleet, order):
    for defect in fleet.defects(order.vehicle_id):
        if defect.order_id == order.id and defect.is_open:
            defect.fixed = order.closed


def record_tread(fleet, vehicle_id, day, position, depth):
    reading = TreadReading(fleet.vehicle(vehicle_id).id, day, position.upper(), depth)
    fleet.add_tread(reading)
    return reading


def latest_treads(fleet, vehicle_id, as_of):
    """The most recent tread reading at each wheel position, on or before `as_of`."""
    latest = {}
    for reading in fleet.treads(vehicle_id):
        if reading.day <= as_of:
            latest[reading.position] = reading
    return [latest[position] for position in sorted(latest)]
