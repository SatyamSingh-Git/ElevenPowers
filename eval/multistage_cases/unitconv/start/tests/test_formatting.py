import pytest

from unitconv import UnitError, convert, format_number, format_quantity, parse_quantity, result_record


@pytest.mark.parametrize('value, text', [(1.5, '1.5'), (2.0, '2'), (1e-05, '0.00001'), (1e20, '100000000000000000000'),
                                         (-0.0, '0')])
def test_format_number(value, text):
    assert format_number(value) == text


def test_symbol_and_name_styles():
    quantity = convert(parse_quantity('1 mi'), 'km')
    assert format_quantity(quantity) == '1.609344 km'
    assert format_quantity(quantity, style='name') == '1.609344 kilometres'
    assert format_quantity(parse_quantity('1 ft'), style='name') == '1 foot'
    with pytest.raises(UnitError, match="unknown style: 'long'"):
        format_quantity(quantity, style='long')


def test_output_reads_back():
    quantity = convert(parse_quantity('1 N'), 'g*cm/s^2')
    again = parse_quantity(format_quantity(quantity))
    assert again.value == quantity.value
    assert again.unit.symbol == quantity.unit.symbol


def test_result_record():
    record = result_record('1 mi', convert(parse_quantity('1 mi'), 'km'))
    assert record == {'input': '1 mi', 'value': 1.609344, 'unit': 'km', 'text': '1.609344 km'}
