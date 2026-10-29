from datetime import date
from decimal import Decimal

import pytest

from fleetkeep.config import load_settings
from fleetkeep.errors import FleetError
from fleetkeep.model.readings import FuelEntry, OdometerReading
from fleetkeep.services import workorders
from fleetkeep.services.inspections import record_tread, report_defect
from fleetkeep.storage.fleetdir import FleetDirectory


def test_round_trip(tmp_path, fleet):
    directory = FleetDirectory(tmp_path / "north")
    directory.create("North")
    fleet.add_reading(OdometerReading("VAN-101", date(2026, 1, 2), 3000))
    fleet.add_fuel(FuelEntry("VAN-101", date(2026, 1, 3), Decimal("20.5"), 7175))
    fleet.assign_card("4417", "VAN-101")
    order = workorders.open_order(fleet, "VAN-101", date(2026, 1, 4), ["OIL"], breakdown=True)
    workorders.receive_parts(fleet, "OF-12", 2, 840, "oil filter")
    workorders.add_part(fleet, order.id, "OF-12", 1)
    workorders.log_labour(fleet, order.id, "Ana", Decimal("1.25"))
    workorders.close_order(fleet, order.id, date(2026, 1, 5))
    report_defect(fleet, "TRK-201", date(2026, 1, 6), "mirror cracked")
    record_tread(fleet, "TRK-201", date(2026, 1, 6), "lf", 9)
    fleet.retire_vehicle("TRK-201", date(2026, 2, 1))
    directory.save(fleet)

    loaded = directory.load()
    assert loaded.vehicles() == fleet.vehicles()
    assert loaded.readings() == fleet.readings()
    assert loaded.fuel() == fleet.fuel()
    assert loaded.orders() == fleet.orders()
    assert loaded.history() == fleet.history()
    assert loaded.stock() == fleet.stock()
    assert loaded.cards() == [("4417", "VAN-101")]
    assert loaded.defects() == fleet.defects()
    assert loaded.treads() == fleet.treads()


def test_settings(tmp_path):
    path = tmp_path / "fleet.ini"
    path.write_text("[fleet]\nname = North\nlabour_rate = 102.50\ndue_soon_days = 21\n")
    settings = load_settings(path)
    assert (settings.name, settings.labour_rate, settings.due_soon_days) == ("North", 10250, 21)
    assert settings.due_soon_miles == 500


@pytest.mark.parametrize("text, code", [("[fleet]\ncolour = red\n", "E151"),
                                        ("[fleet]\ndue_soon_days = soon\n", "E152")])
def test_bad_settings(tmp_path, text, code):
    path = tmp_path / "fleet.ini"
    path.write_text(text)
    with pytest.raises(FleetError) as caught:
        load_settings(path)
    assert caught.value.code == code


def test_no_fleet(tmp_path):
    with pytest.raises(FleetError) as caught:
        FleetDirectory(tmp_path).load()
    assert caught.value.code == "E153"
