import json

import pytest

from unitconv.cli import main


def run(capsys, *argv):
    code = main(list(argv))
    out, err = capsys.readouterr()
    return code, out, err


def test_convert(capsys):
    assert run(capsys, 'convert', '1 mi', 'km') == (0, '1.609344 km\n', '')
    assert run(capsys, 'convert', '1 mi', 'km', '--precision', '1', '--style', 'name') == (0, '1.6 kilometres\n', '')
    assert run(capsys, 'convert', '1.8 m', 'ft+in', '--precision', '1') == (0, '5 ft 10.9 in\n', '')


def test_json(capsys):
    code, out, _ = run(capsys, 'convert', '1 mi', 'km', '--json')
    assert code == 0
    assert json.loads(out) == {'input': '1 mi', 'value': 1.609344, 'unit': 'km', 'text': '1.609344 km'}


def test_settings_file(tmp_path, capsys):
    path = tmp_path / 'unitconv.ini'
    path.write_text('precision = 2\n', encoding='utf-8')
    assert run(capsys, 'convert', '1 mi', 'km', '--settings', str(path))[1] == '1.61 km\n'
    assert run(capsys, 'convert', '1 mi', 'km', '--settings', str(path), '--precision', '0')[1] == '2 km\n'


def test_errors(capsys):
    assert run(capsys, 'convert', '1 mi', 's') == (1, '', 'error: cannot convert mi (length) to s (time)\n')
    assert run(capsys, 'convert', '1 m', 'ft', '--precision', '20')[0] == 1
    with pytest.raises(SystemExit) as exit:
        main(['convert', '1 m'])
    assert exit.value.code == 2


def test_list_and_info(capsys):
    _, out, _ = run(capsys, 'list', '--dimension', 'volume')
    assert [line.split()[0] for line in out.splitlines()] == ['L', 'gal', 'qt']
    _, out, _ = run(capsys, 'info', 'km')
    assert 'factor     1000\n' in out
    assert run(capsys, 'list', '--dimension', 'smell') == (1, '', "error: unknown dimension: 'smell'\n")


def test_batch(tmp_path, capsys):
    source, destination = tmp_path / 'in.csv', tmp_path / 'out.csv'
    source.write_text('1 mi,km\n1 mi,s\n', encoding='utf-8')
    assert run(capsys, 'batch', str(source), str(destination)) == (1, 'converted 1 rows, 1 failed\n', '')
