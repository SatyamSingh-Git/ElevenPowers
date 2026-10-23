import pytest

from unitconv import convert, format_quantity, parse_quantity


@pytest.mark.parametrize('text, target, options, expected', [
    ('0.235 m', 'cm', {'precision': 0}, '24 cm'),
    ('0.285 m', 'cm', {'precision': 0}, '28 cm'),
    ('0.145 m', 'cm', {'precision': 0, 'rounding': 'half_up'}, '15 cm'),
    ('0.565 m', 'cm', {'precision': 0, 'rounding': 'half_up'}, '57 cm'),
    ('1.005 km', 'm', {'precision': 13}, '1005 m'),
])
def test_values_round_as_written(text, target, options, expected):
    assert format_quantity(convert(parse_quantity(text), target), **options) == expected


def test_no_binary_noise_at_full_precision():
    assert format_quantity(convert(parse_quantity('1.005 km'), 'm'), precision=15) == '1005 m'
    assert format_quantity(convert(parse_quantity('0.3 m'), 'mm'), precision=15) == '300 mm'
