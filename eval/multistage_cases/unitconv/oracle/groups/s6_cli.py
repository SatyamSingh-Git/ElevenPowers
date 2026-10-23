import csv
import json

from unitconv.cli import main


def output(capsys, *argv):
    assert main(list(argv)) == 0
    return capsys.readouterr().out


def test_convert_rounds_as_written(capsys):
    assert output(capsys, 'convert', '0.235 m', 'cm', '--precision', '0') == '24 cm\n'
    assert output(capsys, 'convert', '0.145 m', 'cm', '--precision', '0', '--rounding', 'half_up') == '15 cm\n'


def test_json_value_rounds_as_written(capsys):
    record = json.loads(output(capsys, 'convert', '0.235 m', 'cm', '--precision', '0', '--json'))
    assert (record['value'], record['text']) == (24, '24 cm')


def test_batch_rounds_as_written(tmp_path, capsys):
    source, destination = tmp_path / 'in.csv', tmp_path / 'out.csv'
    source.write_text('0.235 m,cm\n1.005 km,m\n', encoding='utf-8')
    output(capsys, 'batch', str(source), str(destination), '--precision', '0', '--rounding', 'half_up')
    with open(destination, newline='', encoding='utf-8') as file:
        assert [row['value'] for row in csv.DictReader(file)] == ['24', '1005']
