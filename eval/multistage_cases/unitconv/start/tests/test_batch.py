import csv

from unitconv import Settings
from unitconv.batch import convert_file


def run_batch(tmp_path, text, settings=Settings()):
    source, destination = tmp_path / 'in.csv', tmp_path / 'out.csv'
    source.write_text(text, encoding='utf-8')
    counts = convert_file(source, destination, settings)
    with open(destination, newline='', encoding='utf-8') as file:
        return counts, list(csv.DictReader(file))


def test_converts_rows(tmp_path):
    counts, rows = run_batch(tmp_path, '# trip\n1 mi,km\n\n100 degC,degF\n')
    assert counts == (2, 0)
    assert [(row['value'], row['unit'], row['error']) for row in rows] == [('1.609344', 'km', ''), ('212', 'degF', '')]


def test_failed_rows_keep_their_reason(tmp_path):
    counts, rows = run_batch(tmp_path, '1 mi,s\n2 xyz,m\n3 m\n')
    assert counts == (0, 3)
    assert [row['error'] for row in rows] == [
        'cannot convert mi (length) to s (time)', "unknown unit: 'xyz'", 'expected 2 columns, got 1']


def test_uses_settings(tmp_path):
    _, rows = run_batch(tmp_path, '1 mi,km\n', Settings(precision=1, rounding='up'))
    assert rows[0]['value'] == '1.7'
