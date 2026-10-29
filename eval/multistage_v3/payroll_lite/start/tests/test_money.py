from decimal import Decimal

import pytest

from payroll.errors import PayrollError
from payroll.model.money import format_money, parse_money, parse_rate, percent_of, plain_money, round_money


def test_rounds_half_up_to_the_cent():
    assert round_money(Decimal("50.625")) == Decimal("50.63")
    assert round_money(Decimal("0.005")) == Decimal("0.01")


def test_parses_amounts_people_type():
    assert parse_money("1,250") == Decimal("1250.00")
    assert parse_money(" 12.5 ") == Decimal("12.50")


def test_rejects_text_that_is_not_an_amount():
    with pytest.raises(PayrollError, match="rate is not an amount: abc"):
        parse_money("abc", "rate")


def test_rate_must_not_be_negative():
    with pytest.raises(PayrollError, match="must not be negative"):
        parse_rate("-1")


def test_percent_of_rounds_the_result():
    assert percent_of(Decimal("1012.50"), Decimal("5")) == Decimal("50.63")


def test_formats_for_people_and_for_files():
    assert format_money(Decimal("2687.776")) == "2,687.78"
    assert plain_money(Decimal("2687.776")) == "2687.78"
