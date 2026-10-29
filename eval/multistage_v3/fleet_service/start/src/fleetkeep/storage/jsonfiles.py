"""Vehicles, work orders, defects and the parts stock, kept as JSON documents."""
from datetime import date
from decimal import Decimal
import json

from ..model.inspection import Defect
from ..model.stock import StockItem
from ..model.vehicle import Vehicle
from ..model.workorder import LabourLine, PartLine, WorkOrder


def vehicle_to_dict(vehicle):
    return {
        "id": vehicle.id,
        "class": vehicle.vehicle_class,
        "make": vehicle.make,
        "model": vehicle.model,
        "year": vehicle.year,
        "in_service": vehicle.in_service.isoformat(),
        "start_odometer": vehicle.start_odometer,
        "retired": vehicle.retired.isoformat() if vehicle.retired else None,
    }


def vehicle_from_dict(data):
    return Vehicle(data["id"], data["class"], data["make"], data["model"], data["year"],
                   date.fromisoformat(data["in_service"]), data["start_odometer"],
                   date.fromisoformat(data["retired"]) if data["retired"] else None)


def order_to_dict(order):
    return {
        "id": order.id,
        "vehicle": order.vehicle_id,
        "opened": order.opened.isoformat(),
        "closed": order.closed.isoformat() if order.closed else None,
        "services": list(order.services),
        "parts": [{"number": p.number, "description": p.description,
                   "quantity": p.quantity, "unit_price": p.unit_price} for p in order.parts],
        "labour": [{"mechanic": l.mechanic, "hours": str(l.hours), "rate": l.rate}
                   for l in order.labour],
        "note": order.note,
        "breakdown": order.breakdown,
    }


def order_from_dict(data):
    return WorkOrder(
        id=data["id"],
        vehicle_id=data["vehicle"],
        opened=date.fromisoformat(data["opened"]),
        services=tuple(data["services"]),
        note=data["note"],
        breakdown=data["breakdown"],
        closed=date.fromisoformat(data["closed"]) if data["closed"] else None,
        parts=[PartLine(p["number"], p["description"], p["quantity"], p["unit_price"])
               for p in data["parts"]],
        labour=[LabourLine(l["mechanic"], Decimal(l["hours"]), l["rate"]) for l in data["labour"]],
    )


def stock_to_dict(item):
    return {"number": item.number, "description": item.description,
            "on_hand": item.on_hand, "unit_cost": item.unit_cost}


def stock_from_dict(data):
    return StockItem(data["number"], data["description"], data["on_hand"], data["unit_cost"])


def defect_to_dict(defect):
    return {"id": defect.id, "vehicle": defect.vehicle_id, "reported": defect.reported.isoformat(),
            "description": defect.description, "severity": defect.severity,
            "order": defect.order_id, "fixed": defect.fixed.isoformat() if defect.fixed else None}


def defect_from_dict(data):
    return Defect(data["id"], data["vehicle"], date.fromisoformat(data["reported"]),
                  data["description"], data["severity"], data["order"],
                  date.fromisoformat(data["fixed"]) if data["fixed"] else None)


def write_documents(path, documents):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(documents, handle, indent=2)
        handle.write("\n")


def read_documents(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)
