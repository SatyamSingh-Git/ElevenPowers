import pytest

from surveytally.cli.config import Settings, load_settings
from surveytally.model.errors import ConfigError


def test_defaults_without_a_file(tmp_path):
    assert load_settings(tmp_path) == Settings(decimals=1, format='csv', min_seconds=0)


def test_values_from_the_file(tmp_path):
    (tmp_path / 'surveytally.ini').write_text('[surveytally]\nformat = markdown\nmin_seconds = 90\n', encoding='utf-8')
    assert load_settings(tmp_path) == Settings(decimals=1, format='markdown', min_seconds=90)


@pytest.mark.parametrize('line, message', [
    ('decimals = two', 'decimals must be a whole number'),
    ('format = xlsx', 'format must be one of csv, markdown, text'),
    ('colour = blue', 'unknown setting colour'),
])
def test_bad_values_are_refused(tmp_path, line, message):
    (tmp_path / 'surveytally.ini').write_text(f'[surveytally]\n{line}\n', encoding='utf-8')
    with pytest.raises(ConfigError, match=message):
        load_settings(tmp_path)
