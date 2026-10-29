from datetime import date

import pytest

from fleetkeep.model.vehicle import Vehicle
from fleetkeep.services.fleet import Fleet


@pytest.fixture
def fleet():
    fleet = Fleet()
    fleet.add_vehicle(Vehicle("VAN-101", "light", "Ford", "Transit", 2025, date(2025, 9, 1), 100))
    fleet.add_vehicle(Vehicle("TRK-201", "heavy", "Volvo", "VNL", 2024, date(2024, 6, 1), 1000))
    return fleet


@pytest.fixture
def write_csv(tmp_path):
    def write(name, text):
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        return path
    return write
