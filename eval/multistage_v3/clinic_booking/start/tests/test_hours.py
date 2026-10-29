from datetime import date

import pytest

from clinicbook.model.hours import OpeningHours, parse_window
from conftest import MONDAY, SUNDAY, at


def test_window_on_an_ordinary_day(clinic):
    assert clinic.hours.window(MONDAY) == (at("09:00"), at("17:00"))
    assert clinic.hours.open_minutes(MONDAY) == 480


def test_sundays_public_holidays_and_closures_are_shut(clinic):
    assert clinic.hours.window(SUNDAY) is None
    assert clinic.hours.closed_reason(date(2026, 4, 3)) == "Good Friday"
    assert clinic.hours.closed_reason(date(2026, 3, 20)) == "closed"
    assert clinic.hours.closed_reason(SUNDAY) == "closed on Sundays"


def test_next_open_day_skips_the_easter_weekend(clinic):
    assert clinic.hours.next_open_day(date(2026, 4, 3)) == date(2026, 4, 4)
    assert clinic.hours.next_open_day(date(2026, 4, 5)) == date(2026, 4, 7)


@pytest.mark.parametrize("text", ["9-5", "09:00", "17:00-09:00", "09:00-25:00"])
def test_bad_windows_are_refused(text):
    with pytest.raises(ValueError):
        parse_window(text)


def test_unknown_weekday_is_refused():
    with pytest.raises(ValueError, match="unknown weekday"):
        OpeningHours.from_spec({"monday": "09:00-17:00"})
