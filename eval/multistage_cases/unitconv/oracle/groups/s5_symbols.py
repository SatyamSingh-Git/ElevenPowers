import json

from unitconv import convert, format_quantity, parse_quantity
from unitconv.cli import main


def test_results_use_middle_dot_and_superscripts():
    assert format_quantity(convert(parse_quantity('1 N'), 'kg*m/s^2')) == '1 kg·m/s²'
    assert format_quantity(convert(parse_quantity('1 J'), 'kg*m^2/s^2')) == '1 kg·m²/s²'
    assert format_quantity(convert(parse_quantity('1 ha'), 'm^2')) == '10000 m²'
    assert format_quantity(convert(parse_quantity('1 L'), 'cm^3')) == '1000 cm³'
    assert format_quantity(convert(parse_quantity('90 km/h'), 'm/s')) == '25 m/s'


def test_command_line_results(capsys):
    assert main(['convert', '1 J', 'kg*m^2/s^2']) == 0
    assert capsys.readouterr().out == '1 kg·m²/s²\n'
    assert main(['convert', '1 ha', 'm^2', '--json']) == 0
    assert json.loads(capsys.readouterr().out)['text'] == '10000 m²'
