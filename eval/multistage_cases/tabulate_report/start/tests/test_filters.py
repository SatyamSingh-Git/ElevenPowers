import pytest

from tabreport import Filter, ReportError, parse_filter
from tabreport.filters import keep


def test_parse_filter():
    assert parse_filter("region=East") == Filter("region", "=", "East")
    assert parse_filter(" amount >= 1,000 ") == Filter("amount", ">=", "1,000")
    assert parse_filter("product!=") == Filter("product", "!=", "")


def test_bad_filters():
    with pytest.raises(ReportError, match="^bad filter: 'amount'$"):
        parse_filter("amount")
    with pytest.raises(ReportError, match="^not a number: 'many'$"):
        parse_filter("amount>many")


def test_keep():
    rows = [{"v": "5"}, {"v": "(20)"}, {"v": ""}, {"v": "$1,500"}]
    assert keep(rows, [parse_filter("v>0")]) == [{"v": "5"}, {"v": "$1,500"}]
    assert keep(rows, [parse_filter("v<=5")]) == [{"v": "5"}, {"v": "(20)"}]
    assert keep(rows, [parse_filter("v=")]) == [{"v": ""}]
