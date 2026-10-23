import csv
import io

from tabreport.cli import main

SALES = """region,product,units,amount
East,Widget,3,1200.50
West,Gadget,1,-150.25
East,Gadget,2,300
North,Widget,5,"1,000.00"
West,Widget,4,99.75
"""


def _run(tmp_path, *options):
    path = tmp_path / "sales.csv"
    path.write_bytes(SALES.encode("utf-8"))
    out = tmp_path / "out.csv"
    assert main([str(path), *options, "-f", "csv", "-o", str(out)]) == 0
    return [row for row in csv.reader(io.StringIO(out.read_text(encoding="utf-8"))) if row]


def test_csv_has_no_rules_or_footer(tmp_path):
    rows = _run(tmp_path, "-g", "region", "-m", "sum:amount", "-m", "count")
    assert len(rows) == 5
    assert rows[0][0] == "region"
    assert rows[1] == ["East", "1500.50", "2"]
    assert rows[-1] == ["TOTAL", "2450.00", "5"]


def test_csv_two_keys_and_no_totals(tmp_path):
    rows = _run(tmp_path, "-g", "region,product", "-m", "max:amount", "--no-totals", "--currency", "eur")
    assert rows[1:] == [
        ["East", "Gadget", "300.00"],
        ["East", "Widget", "1200.50"],
        ["North", "Widget", "1000.00"],
        ["West", "Gadget", "-150.25"],
        ["West", "Widget", "99.75"],
    ]
