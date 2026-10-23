import pytest

from unitconv import convert, format_quantity, parse_quantity, parse_unit
from unitconv.cli import main


def test_new_spelling_is_accepted_as_input():
    assert float(convert(parse_quantity('9.81 m·s⁻²'), 'm/s^2').value) == pytest.approx(9.81)
    assert float(convert(parse_quantity('1 kg·m²/s²'), 'J').value) == pytest.approx(1)
    assert float(convert(parse_quantity('2 m²'), 'cm^2').value) == pytest.approx(20000)
    assert parse_unit('kg·m²/s²').dimension == parse_unit('J').dimension


def test_old_spelling_still_works():
    assert float(convert(parse_quantity('9.81 m*s^-2'), 'm/s^2').value) == pytest.approx(9.81)
    assert float(convert(parse_quantity('1 kg*m^2/s^2'), 'J').value) == pytest.approx(1)


def test_printed_results_read_back(capsys):
    assert main(['convert', '1 kWh', 'kg*m^2/s^2']) == 0
    printed = capsys.readouterr().out.strip()
    assert format_quantity(parse_quantity(printed)) == printed
    assert main(['convert', printed, 'kWh']) == 0
    assert capsys.readouterr().out == '1 kWh\n'
