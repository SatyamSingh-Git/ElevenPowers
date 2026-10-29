from datetime import datetime

import pytest

from boxoffice.clock import FixedClock
from boxoffice.services.boxoffice import BoxOffice

SEATMAP = """\
venue Test Hall
section Stalls tier=A
row A 1-6
row B 1-6 C:5 W:6
section Circle tier=B
row C 1-4
"""

OPENING = datetime(2026, 5, 20, 19, 30)


@pytest.fixture
def clock():
    return FixedClock(datetime(2026, 5, 1, 10, 0))


@pytest.fixture
def office(tmp_path, clock):
    office = BoxOffice(tmp_path, clock)
    office.store.install_venue(SEATMAP)
    office.schedule.add("TEMP-0520", "The Tempest", OPENING, {"A": 3000, "B": 2000})
    return office
