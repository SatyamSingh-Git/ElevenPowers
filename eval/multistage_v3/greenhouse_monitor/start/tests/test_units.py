import pytest

from greenhouse.core.errors import ValidationError
from greenhouse.core.units import check_kind, check_range, format_value, round_for, to_canonical


def test_fahrenheit_is_converted_to_celsius():
    assert to_canonical("temperature", 68.0, "F") == pytest.approx(20.0)


def test_klux_is_converted_to_lux():
    assert to_canonical("light", 12.5, "klux") == pytest.approx(12500.0)


def test_canonical_unit_passes_through():
    assert to_canonical("humidity", 71.0, "%") == 71.0


def test_unit_the_kind_does_not_accept_is_refused():
    with pytest.raises(ValidationError, match="unknown unit F for humidity"):
        to_canonical("humidity", 70.0, "F")


def test_unknown_kind_is_refused():
    with pytest.raises(ValidationError, match="unknown kind: co2"):
        check_kind("co2")


def test_value_outside_catalog_range_is_refused():
    with pytest.raises(ValidationError, match=r"out of range: 104\.0 %"):
        check_range("soil_moisture", 104.0)


def test_values_keep_the_catalog_decimals():
    assert format_value("temperature", 21.04) == "21.0"
    assert format_value("humidity", 70.6) == "71"
    assert round_for("soil_moisture", 33.333) == 33.3
