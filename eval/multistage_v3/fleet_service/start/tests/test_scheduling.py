from datetime import date

from fleetkeep.model.readings import OdometerReading
from fleetkeep.services.reminders import reminders
from fleetkeep.services.scheduling import due_items


def item(items, vehicle, code):
    return next(i for i in items if (i.vehicle_id, i.code) == (vehicle, code))


def test_never_serviced_counts_from_entering_service(fleet):
    fleet.add_reading(OdometerReading("VAN-101", date(2026, 1, 10), 4000))
    oil = item(due_items(fleet, date(2026, 1, 10)), "VAN-101", "OIL")
    assert (oil.due_miles, oil.remaining_miles) == (7600, 3600)
    assert (oil.due_date, oil.remaining_days) == (date(2026, 3, 1), 50)
    assert oil.status == "ok"


def test_due_from_the_last_service(fleet):
    fleet.add_reading(OdometerReading("VAN-101", date(2026, 1, 10), 9000))
    fleet.record_service("VAN-101", "OIL", date(2026, 1, 10), 9000)
    fleet.add_reading(OdometerReading("VAN-101", date(2026, 4, 1), 16200))
    oil = item(due_items(fleet, date(2026, 4, 1)), "VAN-101", "OIL")
    assert (oil.due_miles, oil.remaining_miles, oil.due_date) == (16500, 300, date(2026, 7, 10))
    assert oil.status == "due-soon"


def test_date_only_and_mileage_only_services(fleet):
    items = due_items(fleet, date(2026, 1, 1), "VAN-101")
    wipers = item(items, "VAN-101", "WIPERS")
    rotation = item(items, "VAN-101", "TIRE-ROT")
    assert (wipers.due_miles, wipers.due_date) == (None, date(2026, 9, 1))
    assert (rotation.due_miles, rotation.due_date) == (6100, None)


def test_overdue_comes_first(fleet):
    fleet.add_reading(OdometerReading("VAN-101", date(2026, 2, 1), 7700))
    items = due_items(fleet, date(2026, 2, 1))
    assert [i.status for i in items] == sorted((i.status for i in items),
                                               key=["overdue", "due-soon", "ok"].index)
    assert item(items, "VAN-101", "OIL").status == "overdue"


def test_retired_vehicles_are_not_scheduled(fleet):
    fleet.retire_vehicle("TRK-201", date(2025, 12, 1))
    assert {i.vehicle_id for i in due_items(fleet, date(2026, 1, 1))} == {"VAN-101"}


def test_reminders_for_services_due_soon(fleet):
    fleet.retire_vehicle("TRK-201", date(2025, 12, 1))
    fleet.add_reading(OdometerReading("VAN-101", date(2026, 1, 20), 5800))
    texts = [r.text for r in reminders(fleet, date(2026, 1, 20))]
    assert texts == ["VAN-101: Tyre rotation (TIRE-ROT) is due soon: 300 miles left"]
