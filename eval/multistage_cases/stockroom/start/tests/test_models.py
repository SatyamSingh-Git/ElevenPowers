from decimal import Decimal

import pytest

from stockroom.models import (
    StockError, format_money, normalize_code, normalize_sku, parse_count, parse_money, parse_qty,
)


def test_codes_are_trimmed_and_upper_cased():
    assert normalize_sku(' bolt-m6 ') == 'BOLT-M6'
    assert normalize_code('a1') == 'A1'


@pytest.mark.parametrize('text', ['', '-BOLT', 'BOLT M6', 'X' * 25])
def test_bad_skus_are_refused(text):
    with pytest.raises(StockError, match='invalid sku'):
        normalize_sku(text)


def test_quantities_are_whole_and_positive():
    assert parse_qty('12') == 12
    assert parse_qty(1_000_000) == 1_000_000
    for bad in ('0', '-3', '1.5', 'ten', 1_000_001, True):
        with pytest.raises(StockError, match='quantity must be a whole number from 1 to 1000000'):
            parse_qty(bad)


def test_counts_may_be_zero():
    assert parse_count('0') == 0
    with pytest.raises(StockError, match='count must be'):
        parse_count('-1')


def test_money_round_trips():
    assert parse_money('2.5') == Decimal('2.50')
    assert parse_money('$3') == Decimal('3.00')
    assert format_money(Decimal('1234.5')) == '$1,234.50'
    with pytest.raises(StockError, match='cost must be dollars and cents, like 2.50: 1.234'):
        parse_money('1.234')
