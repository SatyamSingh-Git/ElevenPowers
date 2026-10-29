from datetime import date

import pytest

from fleetkeep.errors import FleetError
from fleetkeep.model.readings import OdometerReading


def reading(day, value, vehicle="VAN-101"):
    return OdometerReading(vehicle, day, value)


def test_readings_must_not_go_backwards(fleet):
    fleet.add_reading(reading(date(2026, 1, 1), 5000))
    with pytest.raises(FleetError) as caught:
        fleet.add_reading(reading(date(2026, 1, 2), 4900))
    assert str(caught.value) == "E105 odometer went backwards for VAN-101: 4900 is below 5000"


def test_readings_must_not_jump_too_far(fleet):
    fleet.add_reading(reading(date(2026, 1, 1), 5000))
    fleet.add_reading(reading(date(2026, 1, 3), 7000))
    with pytest.raises(FleetError) as caught:
        fleet.add_reading(reading(date(2026, 1, 4), 8001))
    assert caught.value.code == "E106"


def test_readings_must_be_in_date_order(fleet):
    fleet.add_reading(reading(date(2026, 1, 10), 5000))
    with pytest.raises(FleetError) as caught:
        fleet.add_reading(reading(date(2026, 1, 9), 5000))
    assert caught.value.code == "E107"


def test_odometer_on_a_day(fleet):
    fleet.add_reading(reading(date(2026, 1, 1), 5000))
    fleet.add_reading(reading(date(2026, 2, 1), 6000))
    assert fleet.odometer_on("VAN-101", date(2025, 12, 31)) == 100
    assert fleet.odometer_on("VAN-101", date(2026, 1, 15)) == 5000
    assert fleet.odometer_on("VAN-101", date(2026, 2, 1)) == 6000


def test_correcting_a_reading(fleet):
    fleet.add_reading(reading(date(2026, 1, 1), 5000))
    fleet.add_reading(reading(date(2026, 1, 10), 6000))
    fleet.correct_reading("VAN-101", date(2026, 1, 1), 5500)
    assert fleet.odometer_on("VAN-101", date(2026, 1, 2)) == 5500
    with pytest.raises(FleetError):
        fleet.correct_reading("VAN-101", date(2026, 1, 1), 6500)
    with pytest.raises(FleetError) as caught:
        fleet.correct_reading("VAN-101", date(2026, 1, 2), 5500)
    assert caught.value.code == "E146"


def test_unknown_vehicle(fleet):
    with pytest.raises(FleetError) as caught:
        fleet.vehicle("VAN-999")
    assert str(caught.value) == "E103 unknown vehicle: VAN-999"


def test_services_must_suit_the_vehicle_class(fleet):
    with pytest.raises(FleetError) as caught:
        fleet.record_service("VAN-101", "DOT-ANNUAL", date(2026, 1, 1), 5000)
    assert caught.value.code == "E124"


def test_last_service_is_the_latest_one(fleet):
    fleet.record_service("VAN-101", "OIL", date(2026, 1, 5), 5000)
    fleet.record_service("VAN-101", "OIL", date(2025, 10, 1), 2000)
    assert fleet.last_service("VAN-101", "OIL").odometer == 5000
    assert fleet.last_service("VAN-101", "TIRE-ROT") is None


def test_retired_vehicles_leave_the_active_list(fleet):
    fleet.retire_vehicle("TRK-201", date(2026, 2, 1))
    assert [v.id for v in fleet.active_vehicles(date(2026, 1, 31))] == ["TRK-201", "VAN-101"]
    assert [v.id for v in fleet.active_vehicles(date(2026, 2, 1))] == ["VAN-101"]
    with pytest.raises(FleetError) as caught:
        fleet.retire_vehicle("VAN-101", date(2025, 1, 1))
    assert caught.value.code == "E109"


def test_fuel_cards(fleet):
    fleet.assign_card("4417", "VAN-101")
    assert fleet.card_vehicle("4417") == "VAN-101"
    with pytest.raises(FleetError) as caught:
        fleet.card_vehicle("9999")
    assert caught.value.code == "E113"
