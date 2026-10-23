import pytest

from ledgerbook import AccountError, Chart


def test_type_comes_from_the_root():
    chart = Chart()
    assert chart.open("Assets:Bank:Checking").type == "asset"
    assert chart.open("Liabilities:Card").type == "liability"
    assert not chart.get("Liabilities:Card").debit_normal
    assert chart.get("Assets:Bank:Checking").parent == "Assets:Bank"


@pytest.mark.parametrize("name", ["Assets", "Cash:Wallet", "Assets:cash", "Assets::Cash", "Assets:Cash "])
def test_malformed_names(name):
    with pytest.raises(AccountError, match="invalid account name"):
        Chart().open(name)


def test_duplicate_and_unknown():
    chart = Chart()
    chart.open("Assets:Cash")
    with pytest.raises(AccountError, match="account already open: Assets:Cash"):
        chart.open("Assets:Cash")
    with pytest.raises(AccountError, match="unknown account: Assets:Bank"):
        chart.get("Assets:Bank")


def test_under_matches_whole_segments():
    chart = Chart()
    for name in ("Assets:Bank", "Assets:Bank:Savings", "Assets:Banknotes"):
        chart.open(name)
    assert [a.name for a in chart.under("Assets:Bank")] == ["Assets:Bank", "Assets:Bank:Savings"]
