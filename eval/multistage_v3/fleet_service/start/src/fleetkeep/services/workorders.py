"""Opening, charging and closing work orders, and the parts stock they draw on."""
from dataclasses import dataclass

from ..errors import FleetError
from ..model.readings import OdometerReading
from ..model.stock import StockItem
from ..model.workorder import LabourLine, PartLine, WorkOrder
from .inspections import assign_defects, fix_defects


@dataclass(frozen=True)
class Charges:
    parts: int
    labour: int
    total: int


def _next_id(fleet):
    numbers = [int(order.id.removeprefix("WO-")) for order in fleet.orders()]
    return f"WO-{max(numbers, default=0) + 1:04d}"


def open_order(fleet, vehicle_id, day, services, note="", breakdown=False, defects=()):
    vehicle = fleet.vehicle(vehicle_id)
    order = WorkOrder(_next_id(fleet), vehicle.id, day, tuple(services), note, breakdown)
    assign_defects(fleet, order, defects)
    fleet.add_order(order)
    return order


def cancel_order(fleet, order_id):
    """Drop an order opened by mistake; one with charges or already closed stays on file."""
    order = fleet.order(order_id)
    if not order.is_open or order.parts or order.labour:
        raise FleetError("E125", order=order.id)
    fleet.remove_order(order.id)


def add_part(fleet, order_id, number, quantity, unit_price=None, description=""):
    """Charge a part to an order, drawing it from stock when the workshop stocks it.

    A stocked part is charged at its average cost unless a price is given; a part
    bought in for the job needs its price.
    """
    order = fleet.order(order_id)
    if not order.is_open:
        raise FleetError("E122", order=order.id)
    item = fleet.stock_item(number)
    if item is None and unit_price is None:
        raise FleetError("E132", number=number)
    if item is not None:
        item.issue(quantity)
        unit_price = item.unit_cost if unit_price is None else unit_price
        description = description or item.description
    line = PartLine(number, description, quantity, unit_price)
    order.add_line(line)
    return line


def receive_parts(fleet, number, quantity, unit_cost, description=""):
    item = fleet.stock_item(number)
    if item is None:
        item = StockItem(number, description)
        fleet.add_stock_item(item)
    elif description:
        item.description = description
    item.receive(quantity, unit_cost)
    return item


def count_stock(fleet, number, on_hand):
    item = fleet.stock_item(number)
    if item is None:
        raise FleetError("E133", number=number)
    item.count(on_hand)
    return item


def log_labour(fleet, order_id, mechanic, hours, rate=None):
    order = fleet.order(order_id)
    if rate is None:
        rate = fleet.settings.labour_rate
    line = LabourLine(mechanic, hours, rate)
    order.add_line(line)
    return line


def close_order(fleet, order_id, day, odometer=None):
    """Close the order, record its services at the closing odometer and fix its defects.

    A closing odometer, when given, is recorded as a reading first; otherwise the
    services are recorded at the vehicle's last reading on that day.
    """
    order = fleet.order(order_id)
    order.close(day)
    if odometer is not None:
        fleet.add_reading(OdometerReading(order.vehicle_id, day, odometer))
    at = fleet.odometer_on(order.vehicle_id, day)
    for code in order.services:
        fleet.record_service(order.vehicle_id, code, day, at, order.id)
    fix_defects(fleet, order)
    return order


def order_charges(order):
    return Charges(order.parts_total, order.labour_total, order.parts_total + order.labour_total)
