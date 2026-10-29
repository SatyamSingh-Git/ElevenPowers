import pytest

from budgetbook.errors import StatementError
from budgetbook.importers import detect_layout, get_layout

from conftest import day

STANDARD = "Date,Description,Amount\n2026-03-02,BAKERY,-4.50\n2026-03-03,ACME LTD,2500.00\n"
DEBIT_CREDIT = "Date,Description,Debit,Credit\n02/03/2026,BAKERY,4.50,\n03/03/2026,ACME LTD,,2500.00\n"
CARD = "Transaction Date,Merchant,Amount,Reference\n03/02/2026,BAKERY,4.50,R1\n03/04/2026,REFUND SHOP,-10.00,R2\n"
APP = ("Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance\n"
       "CARD_PAYMENT,Current,2026-03-02 09:15:00,2026-03-03 10:00:00,BAKERY,-4.50,0.25,GBP,COMPLETED,95.25\n")


def test_standard_layout():
    rows, problems = get_layout("standard").read(STANDARD)
    assert problems == []
    assert [(r.date, r.payee, r.amount) for r in rows] == [
        (day("2026-03-02"), "BAKERY", -450), (day("2026-03-03"), "ACME LTD", 250000)]


def test_debit_credit_layout():
    rows, _ = get_layout("debit_credit").read(DEBIT_CREDIT)
    assert [(r.date, r.amount) for r in rows] == [(day("2026-03-02"), -450), (day("2026-03-03"), 250000)]


def test_card_charges_are_money_out():
    rows, _ = get_layout("card").read(CARD)
    assert [(r.date, r.amount, r.memo) for r in rows] == [
        (day("2026-03-02"), -450, "R1"), (day("2026-03-04"), 1000, "R2")]


def test_app_export_takes_off_the_fee():
    rows, _ = get_layout("app_export").read(APP)
    assert [(r.date, r.amount, r.memo) for r in rows] == [(day("2026-03-02"), -475, "CARD_PAYMENT")]


def test_bad_rows_become_problems():
    text = "Date,Description,Amount\n2026-03-02,BAKERY,lots\n2026-02-30,X,1.00\n,,\n2026-03-04,OK,1.00\n"
    rows, problems = get_layout("standard").read(text)
    assert [r.payee for r in rows] == ["OK"]
    assert [str(p) for p in problems] == ["line 2: invalid amount: lots", "line 3: invalid date: 2026-02-30"]


def test_missing_column():
    with pytest.raises(StatementError, match="standard statement is missing column: Amount"):
        get_layout("standard").read("Date,Description\n2026-03-02,BAKERY\n")


@pytest.mark.parametrize("text, name", [
    (STANDARD, "standard"), (DEBIT_CREDIT, "debit_credit"), (CARD, "card"), (APP, "app_export")])
def test_detect_layout(text, name):
    assert detect_layout(text).name == name


def test_detect_layout_gives_up():
    with pytest.raises(StatementError, match="could not recognise"):
        detect_layout("When,What,How much\n")


def test_unknown_layout():
    with pytest.raises(StatementError, match="unknown layout: bank"):
        get_layout("bank")
