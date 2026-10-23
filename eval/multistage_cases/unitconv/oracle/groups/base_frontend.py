import csv
import json

from unitconv.cli import main


def run(capsys, *argv):
    try:
        code = main(list(argv))
    except SystemExit as exit:
        code = exit.code
    out, err = capsys.readouterr()
    return code, out, err


def test_convert_prints_rounded_results(capsys):
    assert run(capsys, 'convert', '1 mi', 'km') == (0, '1.609344 km\n', '')
    assert run(capsys, 'convert', '1 in', 'km') == (0, '0.000025 km\n', '')
    assert run(capsys, 'convert', '1 mi', 'km', '--precision', '2') == (0, '1.61 km\n', '')
    assert run(capsys, 'convert', '2.5 m', 'm', '--precision', '0') == (0, '2 m\n', '')
    assert run(capsys, 'convert', '2.5 m', 'm', '--precision', '0', '--rounding', 'half_up') == (0, '3 m\n', '')
    assert run(capsys, 'convert', '100 degC', 'degF', '--style', 'name') == (0, '212 degrees Fahrenheit\n', '')


def test_mixed_units(capsys):
    assert run(capsys, 'convert', '1.8 m', 'ft+in') == (0, '5 ft 10.866142 in\n', '')
    assert run(capsys, 'convert', '1.82879 m', 'ft+in', '--precision', '2') == (0, '6 ft 0 in\n', '')
    assert run(capsys, 'convert', '100 min', 'h+min', '--style', 'name') == (0, '1 hour 40 minutes\n', '')


def test_json_record(capsys):
    code, out, _ = run(capsys, 'convert', '1 mi', 'km', '--json', '--precision', '3')
    assert code == 0
    record = json.loads(out)
    assert (record['input'], record['value'], record['text']) == ('1 mi', 1.609, '1.609 km')


def test_settings_file(tmp_path, capsys):
    path = tmp_path / 'unitconv.ini'
    path.write_text('# shared\nprecision = 2\nrounding = up\n', encoding='utf-8')
    assert run(capsys, 'convert', '1 mi', 'km', '--settings', str(path)) == (0, '1.61 km\n', '')
    assert run(capsys, 'convert', '1 mi', 'km', '--settings', str(path), '--precision', '0') == (0, '2 km\n', '')


def test_errors(capsys):
    assert run(capsys, 'convert', '1 mi', 's') == (1, '', 'error: cannot convert mi (length) to s (time)\n')
    assert run(capsys, 'convert', '2 xyz', 'm') == (1, '', "error: unknown unit: 'xyz'\n")
    assert run(capsys, 'convert', '1 m', 'ft', '--precision', '16') == (
        1, '', 'error: precision must be between 0 and 15\n')
    assert run(capsys, 'convert', '1 m')[0] == 2


def test_list_and_info(capsys):
    code, out, _ = run(capsys, 'list', '--dimension', 'volume')
    assert code == 0
    assert {'L', 'gal', 'qt'} <= {line.split()[0] for line in out.splitlines() if line.strip()}
    code, out, _ = run(capsys, 'info', 'km')
    assert code == 0
    assert 'kilometre' in out
    assert any(line.split() == ['factor', '1000'] for line in out.splitlines())


def test_batch(tmp_path, capsys):
    source, destination = tmp_path / 'in.csv', tmp_path / 'out.csv'
    source.write_text('# weekend trip\n1 mi,km\n\n100 degC,degF\n30 N,kN\n1 mi,s\n2 xyz,m\n', encoding='utf-8')
    code, out, _ = run(capsys, 'batch', str(source), str(destination), '--precision', '3')
    assert (code, out) == (1, 'converted 3 rows, 2 failed\n')
    with open(destination, newline='', encoding='utf-8') as file:
        rows = list(csv.DictReader(file))
    assert [(row['input'], row['target'], row['value'], row['unit'], row['error']) for row in rows] == [
        ('1 mi', 'km', '1.609', 'km', ''),
        ('100 degC', 'degF', '212', 'degF', ''),
        ('30 N', 'kN', '0.03', 'kN', ''),
        ('1 mi', 's', '', '', 'cannot convert mi (length) to s (time)'),
        ('2 xyz', 'm', '', '', "unknown unit: 'xyz'"),
    ]
