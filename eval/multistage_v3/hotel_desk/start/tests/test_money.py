from decimal import Decimal

import pytest

from hoteldesk.errors import ValidationError
from hoteldesk.money import adjust, format_money, parse_money, per, tax_on


@pytest.mark.parametrize("text, cents", [("12.50", 1250), ("12.5", 1250), ("7", 700), (" 0.99 ", 99)])
def test_parse_money(text, cents):
    assert parse_money(text) == cents


@pytest.mark.parametrize("text", ["abc", "-1.00", "1.005", "nan"])
def test_parse_money_refuses(text):
    with pytest.raises(ValidationError):
        parse_money(text)


def test_format_money():
    assert format_money(123456) == "1234.56"
    assert format_money(5) == "0.05"
    assert format_money(-250) == "-2.50"


def test_adjust_rounds_to_nearest_cent():
    assert adjust(12000, 10) == 13200
    assert adjust(13200, -15) == 11220
    assert adjust(999, -50) == 500


def test_per():
    assert per(30000, 2) == 15000
    assert per(10000, 3) == 3333
    assert per(500, 0) == 0


def test_tax_on_whole_cents():
    assert tax_on(12000, Decimal("0.1175")) == 1410
    assert tax_on(10000, Decimal("0")) == 0
