import csv

import pytest

from surveytally.model.responses import Response
from surveytally.reports.export import export_crosstab, export_frequencies
from surveytally.services.crosstab import crosstab
from surveytally.services.tally import frequencies


@pytest.fixture
def tables(poll_survey):
    responses = [
        Response('R1', {'region': 'north', 'contact': 'email'}),
        Response('R2', {'region': 'north', 'contact': 'phone'}),
        Response('R3', {'region': 'south', 'contact': 'email', 'comments': 'Nice'}),
        Response('R4', {'contact': 'email'}),
    ]
    return frequencies(poll_survey, responses)


def read_csv(path):
    with open(path, newline='', encoding='utf-8') as handle:
        return list(csv.reader(handle))


def test_csv_export_is_long_format(tmp_path, tables):
    path = tmp_path / 'tables.csv'
    export_frequencies(tables, path)
    header, *rows = read_csv(path)
    assert header == ['question', 'option', 'count', 'percent']
    assert ['region', 'north', '2', '66.7'] in rows
    assert ['region', 'west', '0', '0.0'] in rows
    assert ['region', '(no answer)', '1', ''] in rows
    assert not any(row[0] == 'comments' for row in rows)


def test_csv_export_decimals(tmp_path, tables):
    path = tmp_path / 'tables.csv'
    export_frequencies(tables, path, decimals=0)
    assert ['contact', 'email', '3', '75'] in read_csv(path)


def test_markdown_export_uses_labels(tmp_path, tables):
    path = tmp_path / 'tables.md'
    export_frequencies(tables, path, format='markdown')
    text = path.read_text(encoding='utf-8')
    assert '### contact. Preferred contact' in text
    assert '| Email | 3 | 75.0 |' in text
    assert '| (no answer) | 1 |  |' in text


def test_unknown_format(tmp_path, tables):
    with pytest.raises(ValueError, match='unknown export format xlsx'):
        export_frequencies(tables, tmp_path / 'tables.xlsx', format='xlsx')


def test_crosstab_csv_uses_codes(tmp_path, poll_survey):
    responses = [Response('R1', {'region': 'north', 'contact': 'phone'}),
                 Response('R2', {'region': 'south', 'contact': 'phone'})]
    path = tmp_path / 'tab.csv'
    export_crosstab(crosstab(poll_survey, responses, 'region', 'contact'), path)
    header, north, *_ = read_csv(path)
    assert header == ['region', 'phone', 'email', 'Total']
    assert north == ['north', '50.0', '0.0', '50.0']
