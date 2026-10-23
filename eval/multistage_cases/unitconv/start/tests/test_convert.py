import pytest

from unitconv import IncompatibleUnitsError, SettingsError, convert, parse_quantity


def converted(text, target, **options):
    return convert(parse_quantity(text), target, **options).value


def test_simple_conversions():
    assert converted('1 mi', 'km') == 1.609344
    assert converted('10 N', 'kg*m/s^2') == 10
    assert converted('1 atm', 'kPa') == 101.325
    assert converted('90 km/h', 'm/s') == 25


@pytest.mark.parametrize('text, target, expected', [
    ('100 degC', 'degF', 212),
    ('-40 degF', 'degC', -40),
    ('0 degC', 'K', 273.15),
    ('32 degF', 'degC', 0),
])
def test_temperatures(text, target, expected):
    assert converted(text, target) == pytest.approx(expected)


def test_rounds_to_precision():
    assert converted('1 in', 'km') == 0.000025
    assert converted('1 mi', 'km', precision=2) == 1.61
    assert converted('2.5 m', 'm', precision=0) == 2
    assert converted('2.5 m', 'm', precision=0, rounding='half_up') == 3
    assert converted('1.29 m', 'm', precision=1, rounding='floor') == 1.2


def test_incompatible_dimensions():
    with pytest.raises(IncompatibleUnitsError, match=r'cannot convert mi \(length\) to s \(time\)'):
        converted('1 mi', 's')


def test_precision_limit():
    with pytest.raises(SettingsError, match='precision must be between 0 and 15'):
        converted('1 m', 'ft', precision=16)
