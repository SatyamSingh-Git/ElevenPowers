import pytest

from unitconv import convert, format_quantity, parse_quantity


def test_format_quantity_rounds_to_precision():
    tiny = convert(parse_quantity('1 in'), 'km')
    assert format_quantity(tiny) == '0.000025 km'
    assert format_quantity(tiny, precision=8) == '0.0000254 km'
    assert format_quantity(tiny, precision=2, rounding='up') == '0.01 km'
    assert format_quantity(convert(parse_quantity('1 mi'), 'km'), precision=1, style='name') == '1.6 kilometres'


def test_format_quantity_rounding_modes():
    assert format_quantity(parse_quantity('2.5 m'), precision=0) == '2 m'
    assert format_quantity(parse_quantity('2.5 m'), precision=0, rounding='half_up') == '3 m'
    assert format_quantity(parse_quantity('-2.5 m'), precision=0, rounding='floor') == '-3 m'
    assert format_quantity(parse_quantity('1.29 m'), precision=1, rounding='down') == '1.2 m'


def test_format_quantity_refuses_bad_precision():
    with pytest.raises(ValueError, match='precision must be between 0 and 15'):
        format_quantity(parse_quantity('1 m'), precision=16)
