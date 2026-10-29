from datetime import date

import pytest

from payroll.errors import PayrollError
from payroll.model.period import PayCalendar


def test_weekly_periods_are_numbered_within_the_year():
    calendar = PayCalendar("weekly", date(2026, 1, 5), 3)
    periods = calendar.periods_in_year(2026)
    assert periods[0].id == "2026-W01"
    assert (periods[0].start, periods[0].end, periods[0].pay_date) == (
        date(2026, 1, 5), date(2026, 1, 11), date(2026, 1, 14))
    assert calendar.periods_in_year(2027)[0].start == date(2027, 1, 4)


def test_fortnightly_period_belongs_to_the_year_it_starts_in():
    calendar = PayCalendar("fortnightly", date(2026, 1, 5), 3)
    last = calendar.periods_in_year(2026)[-1]
    assert last.start == date(2026, 12, 21)
    assert calendar.period_containing(date(2027, 1, 2)) == last


def test_monthly_periods_are_calendar_months():
    calendar = PayCalendar("monthly", date(2026, 3, 1), 0)
    assert calendar.period("2026-M03").end == date(2026, 3, 31)
    assert [p.id for p in calendar.periods_in_year(2026)][0] == "2026-M03"


def test_unknown_period_ids_are_refused():
    calendar = PayCalendar("weekly", date(2026, 1, 5), 3)
    for text in ("2026-W60", "2026-M01", "W01", "2025-W01"):
        with pytest.raises(PayrollError, match=f"not a period id: {text}"):
            calendar.period(text)


def test_previous_period():
    calendar = PayCalendar("weekly", date(2026, 1, 5), 3)
    assert calendar.previous(calendar.period("2026-W02")).id == "2026-W01"
    assert calendar.previous(calendar.period("2026-W01")) is None
