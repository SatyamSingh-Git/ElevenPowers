import csv
import json

from unitconv import convert, format_quantity, parse_quantity
from unitconv.cli import main


def test_results_use_middle_dot_and_superscripts():
    assert format_quantity(convert(parse_quantity('1 N'), 'kg*m/s^2')) == '1 kg·m/s²'
    assert format_quantity(convert(parse_quantity('1 J'), 'kg*m^2/s^2')) == '1 kg·m²/s²'
    assert format_quantity(convert(parse_quantity('1 ha'), 'm^2')) == '10000 m²'
    assert format_quantity(convert(parse_quantity('1 L'), 'cm^3')) == '1000 cm³'
    assert format_quantity(convert(parse_quantity('90 km/h'), 'm/s')) == '25 m/s'


def test_command_line_and_json(capsys):
    assert main(['convert', '1 J', 'kg*m^2/s^2']) == 0
    assert capsys.readouterr().out == '1 kg·m²/s²\n'
    assert main(['convert', '9.81 m/s^2', 'km/h^2', '--json', '--precision', '0']) == 0
    assert json.loads(capsys.readouterr().out)['unit']['symbol'] == 'km/h²'


def test_batch_unit_column(tmp_path, capsys):
    source, destination = tmp_path / 'in.csv', tmp_path / 'out.csv'
    source.write_text('1 N,kg*m/s^2\n', encoding='utf-8')
    assert main(['batch', str(source), str(destination)]) == 0
    with open(destination, newline='', encoding='utf-8') as file:
        assert next(csv.DictReader(file))['unit'] == 'kg·m/s²'
