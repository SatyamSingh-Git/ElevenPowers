import json

from unitconv.cli import main


def record(capsys, *argv):
    assert main(['convert', *argv, '--json']) == 0
    return json.loads(capsys.readouterr().out)


def test_unit_is_an_object_with_symbol_and_name(capsys):
    assert record(capsys, '1 mi', 'km')['unit'] == {'symbol': 'km', 'name': 'kilometre'}
    assert record(capsys, '3 ft', 'in')['unit'] == {'symbol': 'in', 'name': 'inch'}
    assert record(capsys, '100 degC', 'degF')['unit'] == {'symbol': 'degF', 'name': 'degree Fahrenheit'}


def test_name_is_singular_whatever_the_style(capsys):
    result = record(capsys, '5 km', 'm', '--style', 'name')
    assert result['unit'] == {'symbol': 'm', 'name': 'metre'}
    assert result['text'] == '5000 metres'
    assert result['value'] == 5000
