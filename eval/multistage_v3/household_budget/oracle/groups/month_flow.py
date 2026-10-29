import csv
import io

from budgetbook.cli import main

FEBRUARY = [
    ("2026-02-01", "ACME LTD", "2500.00", "Salary"),
    ("2026-02-03", "TESCO", "-300.00", "Groceries"),
]
MARCH = [
    ("2026-03-01", "ACME LTD", "2500.00", "Salary"),
    ("2026-03-02", "TESCO", "-120.50", "Groceries"),
    ("2026-03-07", "ZARA", "-80.00", "Clothing"),
    ("2026-03-10", "PIZZA PLACE", "-35.00", "Eating out"),
    ("2026-03-12", "CINEMA", "-24.00", "Entertainment"),
    ("2026-03-16", "TESCO", "-262.00", "Groceries"),
    ("2026-03-21", "ZARA", "30.00", "Clothing"),
]


def bb(capsys, folder, *args):
    code = main(["--dir", str(folder), *args])
    out, err = capsys.readouterr()
    assert code == 0, err
    return out


def section(out, title):
    return [row[1:] for row in csv.reader(io.StringIO(out)) if row and row[0] == title]


def setup(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current", "--opening", "2000.00")
    bb(capsys, folder, "budget", "set", "Groceries", "400.00", "--rollover")
    bb(capsys, folder, "budget", "set", "Clothing", "100.00", "--rollover")
    bb(capsys, folder, "budget", "set", "Eating out", "50.00")
    for date, payee, amount, category in FEBRUARY + MARCH:
        bb(capsys, folder, "add", date, "Current", payee, amount, "--category", category)
    return folder


def status(capsys, folder, month):
    out = bb(capsys, folder, "budget", "status", month, "--format", "csv")
    return {row[0]: dict(zip(("Budget", "Carried", "Spent", "Remaining"), row[1:5]))
            for row in section(out, "Budgets")}


def month_report(capsys, folder, month):
    out = bb(capsys, folder, "report", "month", month, "--format", "csv")
    return dict(section(out, "Summary")), dict(section(out, "Spending by category"))


def test_rollover_carries_into_the_next_month(tmp_path, capsys):
    folder = setup(tmp_path, capsys)
    bb(capsys, folder, "close", "2026-02")
    march = status(capsys, folder, "2026-03")
    assert march["Groceries"] == {"Budget": "400.00", "Carried": "100.00", "Spent": "382.50", "Remaining": "117.50"}
    assert march["Clothing"]["Carried"] == "100.00"
    bb(capsys, folder, "close", "2026-03")
    april = status(capsys, folder, "2026-04")
    assert april["Groceries"] == {"Budget": "400.00", "Carried": "117.50", "Spent": "0.00", "Remaining": "517.50"}
    assert april["Clothing"]["Carried"] == march["Clothing"]["Remaining"]
    assert april["Eating out"]["Carried"] == "0.00"


def test_month_report_agrees_with_budget_status(tmp_path, capsys):
    folder = setup(tmp_path, capsys)
    summary, categories = month_report(capsys, folder, "2026-03")
    march = status(capsys, folder, "2026-03")
    assert summary["Income"] == "2500.00"
    for name in ("Groceries", "Clothing", "Eating out"):
        assert categories[name] == march[name]["Spent"]
    assert categories["Entertainment"] == "24.00"
    total = sum(round(float(amount) * 100) for amount in categories.values())
    assert round(float(summary["Spending"]) * 100) == total


def test_year_report_matches_the_closed_months(tmp_path, capsys):
    folder = setup(tmp_path, capsys)
    february, _ = month_report(capsys, folder, "2026-02")
    march, _ = month_report(capsys, folder, "2026-03")
    bb(capsys, folder, "close", "2026-02")
    bb(capsys, folder, "close", "2026-03")
    out = bb(capsys, folder, "report", "year", "2026", "--format", "csv")
    months = {row[0]: row[1:] for row in section(out, "Months")}
    assert months["2026-02"] == [february["Income"], february["Spending"], february["Net"]]
    assert months["2026-03"] == [march["Income"], march["Spending"], march["Net"]]
    cents = [round(float(months[m][1]) * 100) for m in ("2026-02", "2026-03")]
    assert round(float(months["Total"][1]) * 100) == sum(cents)
    assert sorted(months) == ["2026-02", "2026-03", "Total"]
    spent = dict(section(out, "Budgeted categories"))
    assert spent["Groceries"] == "682.50"
