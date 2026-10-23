import pytest

from unitconv import convert, parse_quantity


def test_convert_returns_the_exact_value():
    assert float(convert(parse_quantity('1 in'), 'km').value) == pytest.approx(2.54e-5, rel=1e-9)
    assert float(convert(parse_quantity('1 mm'), 'mi').value) == pytest.approx(1 / 1609344, rel=1e-9)
    assert float(convert(parse_quantity('1 s'), 'wk').value) == pytest.approx(1 / 604800, rel=1e-9)


def test_chained_conversions_do_not_drift():
    there = convert(parse_quantity('1 in'), 'km')
    assert float(convert(there, 'in').value) == pytest.approx(1, rel=1e-9)
    there = convert(parse_quantity('1 mm'), 'mi')
    assert float(convert(there, 'mm').value) == pytest.approx(1, rel=1e-9)
    there = convert(parse_quantity('7 oz'), 't')
    assert float(convert(there, 'oz').value) == pytest.approx(7, rel=1e-9)
