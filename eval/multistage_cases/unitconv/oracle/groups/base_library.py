import pytest

from unitconv import convert, format_quantity, parse_quantity, parse_unit


def value(text, target):
    return float(convert(parse_quantity(text), target).value)


def message(call, *args):
    with pytest.raises(ValueError) as caught:
        call(*args)
    return str(caught.value)


def test_lengths_and_masses():
    assert value('1 mi', 'km') == pytest.approx(1.609344, abs=1e-9)
    assert value('12 in', 'ft') == pytest.approx(1, abs=1e-9)
    assert value('1000 lb', 'kg') == pytest.approx(453.59237, abs=1e-9)
    assert value('3 ft', 'yd') == pytest.approx(1, abs=1e-9)


def test_prefixes_and_symbols_with_capitals():
    assert value('10 N', 'kg*m/s^2') == pytest.approx(10, abs=1e-9)
    assert value('1 kN', 'N') == pytest.approx(1000, abs=1e-9)
    assert value('1 atm', 'kPa') == pytest.approx(101.325, abs=1e-9)
    assert value('1 kWh', 'MJ') == pytest.approx(3.6, abs=1e-9)
    assert value('2 L', 'mL') == pytest.approx(2000, abs=1e-9)
    assert value('1 BTU', 'J') == pytest.approx(1055.05585262, abs=1e-6)


def test_temperatures():
    assert value('100 degC', 'degF') == pytest.approx(212, abs=1e-9)
    assert value('-40 degF', 'degC') == pytest.approx(-40, abs=1e-9)
    assert value('300 K', 'degC') == pytest.approx(26.85, abs=1e-9)


def test_compound_units():
    assert value('90 km/h', 'm/s') == pytest.approx(25, abs=1e-9)
    assert value('1 W/m^2/K', 'W/cm^2/K') == pytest.approx(0.0001, abs=1e-12)
    assert value('1 ha', 'm^2') == pytest.approx(10000, abs=1e-9)
    assert value('60 1/min', '1/s') == pytest.approx(1, abs=1e-9)


def test_errors():
    assert message(convert, parse_quantity('1 mi'), 's') == 'cannot convert mi (length) to s (time)'
    assert message(parse_quantity, '2 xyz') == "unknown unit: 'xyz'"
    assert message(parse_quantity, 'km') == "cannot parse quantity: 'km'"
    assert message(parse_unit, 'degC/min') == "offset unit 'degC' cannot be combined"


def test_formatting():
    quantity = convert(parse_quantity('1 mi'), 'km')
    assert format_quantity(quantity) == '1.609344 km'
    assert format_quantity(quantity, style='name') == '1.609344 kilometres'
    assert format_quantity(parse_quantity('1 ft'), style='name') == '1 foot'
    assert format_quantity(convert(parse_quantity('1 in'), 'km')) == '0.000025 km'


@pytest.mark.parametrize('text, target', [
    ('1 N', 'g*cm/s^2'),
    ('1 ha', 'm^2'),
    ('3 J', 'N*m'),
    ('1 kWh', 'kg*m^2/s^2'),
    ('2 1/s', '1/min'),
])
def test_printed_results_read_back(text, target):
    printed = format_quantity(convert(parse_quantity(text), target))
    assert format_quantity(parse_quantity(printed)) == printed
