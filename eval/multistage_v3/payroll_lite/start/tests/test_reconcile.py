from decimal import Decimal

import pytest

from payroll.errors import PayrollError
from payroll.services.reconcile import Payment, all_matched, load_statement, reconcile

PAYMENTS = [
    Payment("11-1111-0000001-00", "Ana Lima", Decimal("822.54"), "PAY 2026-W01"),
    Payment("22-2222-0000002-00", "Ben Okafor", Decimal("993.82"), "PAY 2026-W01"),
]


def test_every_payment_found():
    statement = [
        ("11-1111-0000001-00", "PAY 2026-W01", Decimal("822.54")),
        ("22-2222-0000002-00", "PAY 2026-W01", Decimal("993.82")),
        ("44-4444-0000004-00", "RENT JAN", Decimal("1500.00")),
    ]
    results = reconcile(PAYMENTS, statement)
    assert [status for _, _, status in results] == ["matched", "matched"]
    assert all_matched(results)


def test_missing_wrong_and_unexpected():
    statement = [
        ("11-1111-0000001-00", "PAY 2026-W01", Decimal("822.45")),
        ("33-3333-0000003-00", "PAY 2026-W01", Decimal("10.00")),
    ]
    assert reconcile(PAYMENTS, statement) == [
        ("11-1111-0000001-00", "Ana Lima", "wrong amount: paid 822.45, expected 822.54"),
        ("22-2222-0000002-00", "Ben Okafor", "missing"),
        ("33-3333-0000003-00", "PAY 2026-W01", "unexpected"),
    ]


def test_statement_needs_its_columns(tmp_path):
    path = tmp_path / "statement.csv"
    path.write_text("date,account,amount\n", encoding="utf-8")
    with pytest.raises(PayrollError, match="statement is missing column reference"):
        load_statement(path)
