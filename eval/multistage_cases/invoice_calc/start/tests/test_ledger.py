import json
from decimal import Decimal

from invoicekit.__main__ import main
from invoicekit.export import read_records, to_record, write_records
from invoicekit.invoice import invoice_from_dict
from invoicekit.ledger import render_ledger, summarize


def invoice(number, region="US-NY", currency="USD", price="10.00", **extra):
    return invoice_from_dict({"number": number, "issued": "2026-05-01", "region": region, "currency": currency,
                              "lines": [{"sku": "A", "description": "a", "quantity": 2, "unit_price": price}],
                              **extra})


def test_records_round_trip(tmp_path):
    records = [to_record(invoice("A-1")), to_record(invoice("A-2", region="DE", currency="EUR"))]
    write_records(tmp_path / "out.jsonl", records)
    assert read_records(tmp_path / "out.jsonl") == records


def test_summarize_by_region_and_currency():
    records = [to_record(invoice("A-1")), to_record(invoice("A-2", discounts=[{"kind": "amount", "amount": "4"}])),
               to_record(invoice("A-3", region="DE", currency="EUR"))]
    rows = summarize(records)
    assert [(row.region, row.currency, row.invoices) for row in rows] == [("DE", "EUR", 1), ("US-NY", "USD", 2)]
    us = rows[1]
    assert (us.subtotal, us.discount, us.tax, us.total) == (
        Decimal("40.00"), Decimal("4.00"), Decimal("3.20"), Decimal("39.20"))
    text = render_ledger(rows)
    assert "-$4.00" in text and "$39.20" in text and "€23.80" in text


def test_cli_export_then_ledger(tmp_path, capsys):
    source = tmp_path / "a.json"
    source.write_text(json.dumps({"number": "A-1", "issued": "2026-05-01", "region": "GB", "currency": "GBP",
                                  "lines": [{"sku": "A", "description": "a", "quantity": 1, "unit_price": "5"}]}),
                      encoding="utf-8")
    assert main(["export", str(tmp_path / "r.jsonl"), str(source)]) == 0
    assert main(["ledger", str(tmp_path / "r.jsonl")]) == 0
    assert "£6.00" in capsys.readouterr().out


def test_cli_reports_bad_input(tmp_path, capsys):
    source = tmp_path / "a.json"
    source.write_text(json.dumps({"number": "A-1", "region": "XX", "lines": []}), encoding="utf-8")
    assert main(["render", str(source)]) == 1
    assert capsys.readouterr().err.startswith("invoicekit: ")
