from datetime import date, datetime, time

import pytest

from parcelpost.core.address import make_address, normalise_postcode, postcode_area
from parcelpost.core.calendar import add_business_days, ship_date
from parcelpost.core.errors import ValidationError
from parcelpost.core.money import format_amount, parse_amount, percent_of
from parcelpost.core.parcel import Parcel, validate_parcel
from parcelpost.core.units import format_kg, kg_to_grams, parse_size


@pytest.mark.parametrize("text, pence", [("12.50", 1250), ("0", 0), ("7", 700), (" 3.05 ", 305)])
def test_parse_amount(text, pence):
    assert parse_amount(text) == pence


@pytest.mark.parametrize("text", ["12.345", "-1", "abc", "NaN"])
def test_parse_amount_refuses(text):
    with pytest.raises(ValidationError, match="invalid amount"):
        parse_amount(text)


def test_format_amount():
    assert format_amount(1250) == "12.50"
    assert format_amount(5) == "0.05"
    assert format_amount(-120) == "-1.20"


def test_percent_of_rounds_half_up():
    assert percent_of(1000, "7.5") == 75
    assert percent_of(1010, "7.5") == 76  # 75.75
    assert percent_of(1006, "7.5") == 75  # 75.45


def test_weights():
    assert kg_to_grams("2.5") == 2500
    assert kg_to_grams("0.001") == 1
    assert format_kg(2500) == "2.5"
    assert format_kg(30000) == "30"
    assert format_kg(1050) == "1.05"
    with pytest.raises(ValidationError):
        kg_to_grams("0")


def test_parse_size():
    assert parse_size("40x30x20") == (40, 30, 20)
    with pytest.raises(ValidationError, match="invalid size"):
        parse_size("40x30")


@pytest.mark.parametrize("text", ["sw1a1aa", "SW1A 1AA", " sw1a  1aa"])
def test_postcodes_are_normalised(text):
    assert normalise_postcode(text) == "SW1A 1AA"
    assert postcode_area("SW1A 1AA") == "SW"


def test_bad_postcode():
    with pytest.raises(ValidationError, match="invalid postcode: 12345"):
        normalise_postcode("12345")


def test_address_fields_are_required_and_bounded():
    with pytest.raises(ValidationError, match="town is required"):
        make_address("Ann", "1 High St", " ", "B1 1AA")
    with pytest.raises(ValidationError, match="name is longer than 35 characters"):
        make_address("A" * 36, "1 High St", "Birmingham", "B1 1AA")


def test_parcel_limits():
    validate_parcel(Parcel(29_999, 150, 10, 10))
    with pytest.raises(ValidationError, match="parcel too long: 151 cm"):
        validate_parcel(Parcel(1000, 151, 10, 10))
    with pytest.raises(ValidationError, match="declared value 2600.00 is over the limit of 2500.00"):
        validate_parcel(Parcel(1000, 10, 10, 10, declared_pence=260_000))
    with pytest.raises(ValidationError, match="too heavy"):
        validate_parcel(Parcel(31_000, 10, 10, 10))


def test_ship_date_respects_cutoff_and_weekends():
    cutoff = time(17, 0)
    assert ship_date(datetime(2026, 3, 2, 16, 59), cutoff) == date(2026, 3, 2)
    assert ship_date(datetime(2026, 3, 2, 17, 0), cutoff) == date(2026, 3, 3)
    assert ship_date(datetime(2026, 3, 6, 18, 0), cutoff) == date(2026, 3, 9)
    assert ship_date(datetime(2026, 3, 7, 9, 0), cutoff) == date(2026, 3, 9)


def test_add_business_days_skips_weekends():
    assert add_business_days(date(2026, 3, 5), 3) == date(2026, 3, 10)
