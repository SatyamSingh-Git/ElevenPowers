import pytest

from unitconv import ParseError, UnitError, parse_quantity, parse_unit


@pytest.mark.parametrize('text, value, symbol', [
    ('12.5 km/h', 12.5, 'km/h'),
    ('-40 degF', -40, 'degF'),
    ('3e3 m', 3000, 'm'),
    ('.5 lb', 0.5, 'lb'),
    ('9.81 m*s^-2', 9.81, 'm/s^2'),
    ('2 1/s', 2, '1/s'),
])
def test_parse_quantity(text, value, symbol):
    quantity = parse_quantity(text)
    assert quantity.value == pytest.approx(value)
    assert quantity.unit.symbol == symbol


@pytest.mark.parametrize('text', ['km', '12', '1,5 m', '5 m 3'])
def test_unparseable_quantity(text):
    with pytest.raises(ParseError, match=f"cannot parse quantity: '{text}'"):
        parse_quantity(text)


def test_repeated_units_merge():
    assert parse_unit('m*m').symbol == 'm^2'
    with pytest.raises(ParseError, match="cannot parse unit: 'm/m'"):
        parse_unit('m/m')


def test_offset_units_stand_alone():
    with pytest.raises(UnitError, match="offset unit 'degC' cannot be combined"):
        parse_unit('degC/min')
