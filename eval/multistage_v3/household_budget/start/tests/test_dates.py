import datetime as dt

import pytest

from budgetbook.errors import ValidationError
from budgetbook.model.dates import Month, months_between, parse_date


def test_parse_date_styles():
    assert parse_date("2026-03-04") == dt.date(2026, 3, 4)
    assert parse_date("04/03/2026", "dmy") == dt.date(2026, 3, 4)
    assert parse_date("03/04/2026", "mdy") == dt.date(2026, 3, 4)
    assert parse_date("2026-03-04 18:30:00", "iso_time") == dt.date(2026, 3, 4)


def test_parse_date_refuses_wrong_style():
    with pytest.raises(ValidationError, match="invalid date: 04/03/2026"):
        parse_date("04/03/2026")


def test_month_arithmetic():
    assert Month.parse("2026-12").next() == Month(2027, 1)
    assert Month.parse("2026-01").previous() == Month(2025, 12)
    assert str(Month(2026, 3)) == "2026-03"
    assert dt.date(2026, 3, 31) in Month(2026, 3)
    assert dt.date(2026, 4, 1) not in Month(2026, 3)


def test_month_day_clamps_to_short_months():
    assert Month(2026, 2).day(31) == dt.date(2026, 2, 28)
    assert Month(2028, 2).day(30) == dt.date(2028, 2, 29)
    assert Month(2026, 1).day(31) == dt.date(2026, 1, 31)


@pytest.mark.parametrize("text", ["2026-13", "2026-3", "March"])
def test_month_parse_refuses(text):
    with pytest.raises(ValidationError, match="invalid month"):
        Month.parse(text)


def test_months_between():
    months = list(months_between(dt.date(2025, 11, 20), dt.date(2026, 2, 1)))
    assert [str(m) for m in months] == ["2025-11", "2025-12", "2026-01", "2026-02"]
