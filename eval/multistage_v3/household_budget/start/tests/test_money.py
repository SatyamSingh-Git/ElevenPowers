import pytest

from budgetbook.errors import ValidationError
from budgetbook.model.money import decimal_text, format_amount, parse_amount, share


@pytest.mark.parametrize("text, cents", [
    ("12.50", 1250),
    ("-12.50", -1250),
    ("1,204.00", 120400),
    ("(3.25)", -325),
    ("  7 ", 700),
    ("0.5", 50),
])
def test_parse_amount(text, cents):
    assert parse_amount(text) == cents


@pytest.mark.parametrize("text", ["", "abc", "12.50.1", "nan", "inf"])
def test_parse_amount_refuses_nonsense(text):
    with pytest.raises(ValidationError, match="invalid amount"):
        parse_amount(text)


def test_format_amount_groups_thousands():
    assert format_amount(-123456) == "-1,234.56"
    assert format_amount(5) == "0.05"


def test_decimal_text_is_plain():
    assert decimal_text(-123456) == "-1234.56"
    assert decimal_text(0) == "0.00"


def test_share():
    assert share(50, 200) == 25
    assert share(1, 0) is None
