"""Work orders, defects and service history as reports."""
from ..model.catalog import service_spec


def order_rows(fleet, vehicle_id=None, open_only=False):
    return [(order.id, order.vehicle_id, order.status, order.opened, order.closed,
             " ".join(order.services))
            for order in fleet.orders(vehicle_id)
            if order.is_open or not open_only]


def history_rows(fleet, vehicle_id):
    return [(record.day, record.code, service_spec(record.code).name, record.odometer,
             record.order_id or None)
            for record in fleet.history(vehicle_id)]


def defect_rows(fleet, vehicle_id=None, open_only=False):
    return [(defect.id, defect.vehicle_id, defect.reported, defect.severity, defect.description,
             defect.order_id or None, defect.fixed)
            for defect in fleet.defects(vehicle_id)
            if defect.is_open or not open_only]
