import pytest

from unitconv import convert, parse_quantity
from unitconv.cli import main


def value(text, target):
    return float(convert(parse_quantity(text), target).value)


def test_prefix_case_is_respected():
    assert value('3 Mm', 'km') == pytest.approx(3000, rel=1e-9)
    assert value('3 mm', 'km') == pytest.approx(0.000003, rel=1e-9)
    assert value('5 MN', 'kN') == pytest.approx(5000, rel=1e-9)
    assert value('2 mN', 'N') == pytest.approx(0.002, rel=1e-9)
    assert value('4 Ms', 's') == pytest.approx(4e6, rel=1e-9)
    assert value('2 MW', 'kW') == pytest.approx(2000, rel=1e-9)


def test_command_line_reads_megametres(capsys):
    assert main(['convert', '3 Mm', 'km']) == 0
    assert capsys.readouterr().out == '3000 km\n'
