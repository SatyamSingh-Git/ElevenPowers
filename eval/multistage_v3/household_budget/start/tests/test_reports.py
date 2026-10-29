import json

from budgetbook.model.dates import Month
from budgetbook.model.records import Account, Transaction
from budgetbook.reports.annual import year_report
from budgetbook.reports.month_end import month_report, summarise
from budgetbook.reports.register import account_register
from budgetbook.reports.render import Report, Section, render_csv, render_markdown, render_text
from budgetbook.services.catalog import Catalog

from conftest import day


def _txn(number, date, payee, amount, category=""):
    return Transaction(number, day(date), "Current", payee, amount, category)


MARCH = [
    _txn(1, "2026-03-01", "ACME LTD", 250000, "Salary"),
    _txn(2, "2026-03-02", "TESCO", -12050, "Groceries"),
    _txn(3, "2026-03-05", "TESCO", -4000, "Groceries"),
    _txn(4, "2026-03-06", "CINEMA", -2400, "Entertainment"),
    _txn(5, "2026-03-07", "MYSTERY", -1000),
    _txn(6, "2026-03-08", "SAVINGS POT", -50000, "Transfer"),
]


def test_summarise():
    summary = summarise(MARCH, Catalog())
    assert summary.income == 250000
    assert summary.spending == 19450
    assert summary.categories == [("Groceries", 16050), ("Entertainment", 2400), ("Uncategorised", 1000)]
    assert summary.payees[0] == ("TESCO", 16050)
    assert summary.net == 230550


def test_month_report_sections():
    report = month_report(Month(2026, 3), MARCH, Catalog(), "GBP")
    assert report.title == "Month end 2026-03 (GBP)"
    assert [s.title for s in report.sections] == ["Summary", "Spending by category", "Top payees"]


def test_render_formats():
    report = Report("T", [Section("S", ("Name", "Amount"), [("Rent", -95000)], amounts=("Amount",))])
    assert "Rent  -950.00" in render_text(report)
    assert render_csv(report) == "section,Name,Amount\nS,Rent,-950.00\n"
    assert "| Rent | -950.00 |" in render_markdown(report)


def test_render_text_large_amounts_are_grouped():
    report = Report("T", [Section("S", ("Name", "Amount"), [("Car", -1250000)], amounts=("Amount",))])
    assert "-12,500.00" in render_text(report)


def test_register_running_balance():
    account = Account("Current", "checking", 10000)
    report = account_register(account, MARCH[:3], Month(2026, 3))
    rows = report.sections[0].rows
    assert [row[-1] for row in rows] == [260000, 247950, 243950]


def test_year_report_reads_month_files(book):
    for month, income, spending in (("2026-01", 250000, 180000), ("2026-02", 250000, 200000)):
        book.closed_month_path(month).write_text(json.dumps({
            "format": 1, "month": month, "currency": "GBP", "income": income, "spending": spending,
            "categories": [{"name": "Groceries", "group": "essentials", "budget": 40000, "carried": 0,
                            "spent": 30000, "remaining": 10000}],
        }), encoding="utf-8")
    report = year_report(book, 2026, "GBP")
    months, categories = report.sections
    assert months.rows == [("2026-01", 250000, 180000, 70000), ("2026-02", 250000, 200000, 50000),
                           ("Total", 500000, 380000, 120000)]
    assert categories.rows == [("Groceries", 60000)]
