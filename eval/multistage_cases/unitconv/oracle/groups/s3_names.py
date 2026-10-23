import json

from unitconv.cli import main


def unit(capsys, *argv):
    assert main(['convert', *argv, '--json']) == 0
    return json.loads(capsys.readouterr().out)['unit']


def test_compound_units_get_their_spoken_name(capsys):
    assert unit(capsys, '10 m/s', 'km/h')['name'] == 'kilometre per hour'
    assert unit(capsys, '1 N', 'kg*m/s^2')['name'] == 'kilogram metre per second squared'
    assert unit(capsys, '1 Pa', 'N/m^2')['name'] == 'newton per metre squared'


def test_prefixed_units_get_their_full_name(capsys):
    assert unit(capsys, '1 kWh', 'MJ') == {'symbol': 'MJ', 'name': 'megajoule'}
    assert unit(capsys, '1 L', 'mL') == {'symbol': 'mL', 'name': 'millilitre'}
