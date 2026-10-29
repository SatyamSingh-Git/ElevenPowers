from datetime import date
from decimal import Decimal

import pytest

from fleetkeep.errors import FleetError
from fleetkeep.importers.fuelcard import import_fuel_card
from fleetkeep.importers.history import import_history
from fleetkeep.importers.telematics import import_telematics
from fleetkeep.importers.timesheets import import_timesheet
from fleetkeep.importers.vehicles import import_vehicles
from fleetkeep.services import workorders


def test_fuel_card_export(fleet, write_csv):
    fleet.assign_card("4417", "TRK-201")
    path = write_csv("fuel.csv", "Card,Unit,Date,Gallons,Amount,Odometer\n"
                                 "1,van-101,01/06/2026,20.5,$71.75,3150\n"
                                 "4417,,01/07/2026,90,\"$1,204.50\",0\n"
                                 "1,VAN-101,01/06/2026,20.5,$71.75,3150\n"
                                 "1,VAN-101,13/20/2026,18,$63.00,\n")
    result = import_fuel_card(fleet, path)
    assert result.imported == 2
    assert result.skipped == [(4, "already imported")]
    assert result.rejected == [(5, "E142 invalid date: 13/20/2026")]
    truck = fleet.fuel("TRK-201")[0]
    assert (truck.gallons, truck.cost, truck.odometer) == (Decimal("90.000"), 120450, None)


def test_missing_columns(fleet, write_csv):
    path = write_csv("fuel.csv", "Card,Unit,Date\n")
    with pytest.raises(FleetError) as caught:
        import_fuel_card(fleet, path)
    assert caught.value.code == "E145"


def test_history_from_the_old_system(fleet, write_csv):
    path = write_csv("history.csv", "vehicle,code,date,odometer\n"
                                    "VAN-101,oil,2025-11-01,2400\n"
                                    "VAN-999,OIL,2025-11-01,2400\n"
                                    "TRK-201,AIR-BRAKE,2025-12-01,40000\n")
    result = import_history(fleet, path)
    assert (result.imported, result.skipped) == (2, [])
    assert result.rejected == [(3, "E103 unknown vehicle: VAN-999")]
    assert fleet.last_service("VAN-101", "OIL").odometer == 2400


def test_timesheet_goes_in_whole(fleet, write_csv):
    order = workorders.open_order(fleet, "VAN-101", date(2026, 1, 5), ["OIL"])
    path = write_csv("week.csv", "order,mechanic,hours,rate\n"
                                 f"{order.id},Ana,1.5,\n"
                                 f"{order.id},Ben,2,120.00\n")
    result = import_timesheet(fleet, path)
    assert result.imported == 2
    assert [(line.mechanic, line.rate) for line in order.labour] == [("Ana", 9500), ("Ben", 12000)]


def test_timesheet_with_a_bad_row_charges_nothing(fleet, write_csv):
    order = workorders.open_order(fleet, "VAN-101", date(2026, 1, 5), ["OIL"])
    path = write_csv("week.csv", "order,mechanic,hours,rate\n"
                                 f"{order.id},Ana,1.5,\n"
                                 "WO-0099,Ben,2,\n")
    result = import_timesheet(fleet, path)
    assert result.imported == 0
    assert result.rejected == [(3, "E121 unknown work order: WO-0099")]
    assert order.labour == []


def test_telematics_keeps_the_last_report_of_each_day(fleet, write_csv):
    path = write_csv("units.csv", "vehicle,timestamp,odometer\n"
                                  "VAN-101,2026-01-05T08:00:00,3000\n"
                                  "VAN-101,2026-01-05T17:30:00,3100\n"
                                  "VAN-101,2026-01-04T09:00:00,2900\n")
    result = import_telematics(fleet, path)
    assert result.imported == 2
    assert result.skipped == [(2, "a later report that day")]
    assert [(r.day, r.odometer) for r in fleet.readings("VAN-101")] == [
        (date(2026, 1, 4), 2900), (date(2026, 1, 5), 3100)]


def test_delivery_schedule(fleet, write_csv):
    path = write_csv("deliveries.csv", "id,class,make,model,year,in_service,odometer\n"
                                       "VAN-101,light,Ford,Transit,2025,2025-09-01,100\n"
                                       "VAN-102,Light,Ford,Transit,2026,2026-01-15,\n")
    result = import_vehicles(fleet, path)
    assert result.imported == 1
    assert result.skipped == [(2, "already in the fleet: VAN-101")]
    assert fleet.vehicle("VAN-102").vehicle_class == "light"
