import pytest

from unitconv import Settings, SettingsError, load_settings


def test_defaults():
    assert Settings() == Settings(precision=6, rounding='half_even', style='symbol')


def test_load_settings(tmp_path):
    path = tmp_path / 'unitconv.ini'
    path.write_text('# house style\nprecision = 3\nrounding = half_up  # finance\n\nstyle=name\n', encoding='utf-8')
    assert load_settings(path) == Settings(precision=3, rounding='half_up', style='name')


@pytest.mark.parametrize('text, message', [
    ('colour = red\n', "unknown setting: 'colour'"),
    ('precision\n', "line 1: expected 'key = value'"),
    ('precision = many\n', 'precision must be between 0 and 15'),
    ('rounding = sideways\n', "unknown rounding mode: 'sideways'"),
])
def test_bad_settings(tmp_path, text, message):
    path = tmp_path / 'unitconv.ini'
    path.write_text(text, encoding='utf-8')
    with pytest.raises(SettingsError, match=message):
        load_settings(path)
