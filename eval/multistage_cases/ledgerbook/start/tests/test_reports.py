from ledgerbook import render_statement, render_trial_balance, statement, summary, trial_balance


def test_trial_balance(household):
    report = trial_balance(household)
    rows = {row.account: (row.debit, row.credit) for row in report.rows}
    assert rows["Assets:Bank"] == (400000, 0)
    assert rows["Liabilities:Card"] == (0, 4250)
    assert rows["Income:Salary"] == (0, 320000)
    assert report.balanced and report.total_debit == 574250


def test_render_trial_balance(household):
    text = render_trial_balance(household)
    assert "Liabilities:Card" in text
    assert text.splitlines()[-1].split() == ["Total", "5742.50", "5742.50"]


def test_statement_running_balance(household):
    lines = statement(household, "Assets:Bank")
    assert [line.balance for line in lines] == [250000, 570000, 420000, 400000]
    assert lines[2].description == "Rent"


def test_render_statement(household):
    text = render_statement(household, "Assets:Cash")
    assert text.splitlines()[0] == "Assets:Cash"
    assert text.splitlines()[-1].split() == ["2026-02-02", "Cash", "withdrawal", "200.00", "200.00"]


def test_summary(household):
    assert summary(household) == {
        "assets": 420000, "liabilities": 4250, "equity": 250000,
        "income": 320000, "expenses": 154250, "net_income": 165750,
    }
