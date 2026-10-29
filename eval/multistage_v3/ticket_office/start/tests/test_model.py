import pytest

from boxoffice.errors import BoxOfficeError
from boxoffice.model.concessions import concession_price
from boxoffice.model.customer import normalise_email
from boxoffice.model.money import format_pence, parse_price
from boxoffice.model.seat_ranges import compress_seats, expand_seats


def test_format_pence():
    assert format_pence(3250) == "32.50"
    assert format_pence(5) == "0.05"
    assert format_pence(-400) == "-4.00"


@pytest.mark.parametrize("text, pence", [("32.50", 3250), ("32", 3200), ("0.5", 50), (" 7.05 ", 705)])
def test_parse_price(text, pence):
    assert parse_price(text) == pence


@pytest.mark.parametrize("text", ["", "-3", "3.505", "three", "3.x"])
def test_parse_price_refuses(text):
    with pytest.raises(ValueError):
        parse_price(text)


def test_concession_prices():
    assert concession_price(3000, "adult") == 3000
    assert concession_price(3000, "child") == 1500
    assert concession_price(2550, "child") == 1275
    assert concession_price(2550, "senior") == 2040


def test_unknown_concession():
    with pytest.raises(BoxOfficeError) as raised:
        concession_price(3000, "pensioner")
    assert raised.value.code == "unknown-concession"
    assert str(raised.value) == "unknown concession pensioner"


def test_seat_ranges():
    assert expand_seats(["A1-A3", "b7"]) == ["A1", "A2", "A3", "B7"]
    assert expand_seats(["C4-C2"]) == ["C4", "C3", "C2"]
    assert expand_seats(["A1-B2"]) == ["A1-B2"]
    assert compress_seats(["A1", "A2", "A3", "A4", "B1", "B3"]) == "A1-A4 B1 B3"
    assert compress_seats(["A1", "A2"]) == "A1 A2"


def test_emails_are_normalised():
    assert normalise_email(" Ann@Example.COM ") == "ann@example.com"
    with pytest.raises(BoxOfficeError):
        normalise_email("ann at example")
