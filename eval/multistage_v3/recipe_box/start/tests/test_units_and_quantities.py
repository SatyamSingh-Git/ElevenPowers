from fractions import Fraction

import pytest

from recipebox.core import units
from recipebox.core.quantity import (
    Quantity, display_amount, display_quantity, format_amount, parse_amount, parse_quantity,
)
from recipebox.errors import AmountError, UnitError


@pytest.mark.parametrize("text, symbol", [
    ("grams", "g"), ("Tbsp.", "tbsp"), ("teaspoons", "tsp"), ("cups", "cup"), ("L", "l"), ("cloves", "clove"),
])
def test_unit_aliases(text, symbol):
    assert units.lookup(text).symbol == symbol


def test_unknown_unit():
    assert units.lookup("handful") is None
    with pytest.raises(UnitError, match="unknown unit handful"):
        units.unit("handful")


def test_convert_within_a_dimension():
    assert units.convert(Fraction(2), "kg", "g") == 2000
    assert units.convert(Fraction(1), "tbsp", "tsp") == Fraction("14.7868") / Fraction("4.92892")


def test_counts_only_combine_with_themselves():
    assert units.convertible("clove", "clove")
    assert not units.convertible("clove", "")
    with pytest.raises(UnitError, match="cannot convert g to ml"):
        units.convert(Fraction(1), "g", "ml")


@pytest.mark.parametrize("text, value", [
    ("2", Fraction(2)), ("0.75", Fraction(3, 4)), ("3/4", Fraction(3, 4)),
    ("1 1/2", Fraction(3, 2)), ("1½", Fraction(3, 2)), ("¼", Fraction(1, 4)),
])
def test_parse_amount(text, value):
    assert parse_amount(text) == value


@pytest.mark.parametrize("text", ["", "a", "1/0", "0", "1 2 3"])
def test_parse_amount_rejects(text):
    with pytest.raises(AmountError, match="cannot read amount"):
        parse_amount(text)


def test_parse_quantity():
    assert parse_quantity("500 g") == Quantity(Fraction(500), "g")
    assert parse_quantity("1 1/2 cups") == Quantity(Fraction(3, 2), "cup")
    assert parse_quantity("3") == Quantity(Fraction(3), "")


def test_format_amount_is_exact():
    assert format_amount(Fraction(3, 2)) == "1 1/2"
    assert format_amount(Fraction(2, 3)) == "2/3"
    assert format_amount(Fraction(4)) == "4"


def test_display_rounds_to_eighths_for_cooks():
    assert display_amount(Fraction(3, 4), "cup") == "3/4"
    assert display_amount(Fraction(13, 10), "cup") == "1 1/4"
    assert display_amount(Fraction(1, 100), "tsp") == "1/8"


def test_display_metric():
    assert display_amount(Fraction(2501, 10), "g") == "250"
    assert display_amount(Fraction(1, 3), "ml") == "1"
    assert display_amount(Fraction(5, 4), "kg") == "1.25"
    assert display_amount(Fraction(3, 2), "l") == "1.5"


def test_display_quantity_without_unit():
    assert display_quantity(Quantity(Fraction(2), "")) == "2"
    assert display_quantity(Quantity(Fraction(1, 2), "cup")) == "1/2 cup"
