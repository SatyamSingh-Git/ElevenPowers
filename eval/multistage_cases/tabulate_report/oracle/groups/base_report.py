from decimal import Decimal

from tabreport import build_report, read_csv, render_report
from tabreport.cli import main

SALES = """region,product,units,amount
East,Widget,3,1200.50
West,Gadget,1,-150.25
East,Gadget,2,300

North,Widget,5,"1,000.00"
West,Widget,4,99.75
"""
MEASURES = ["sum:amount", "count", "mean:amount"]


def _sales(tmp_path):
    path = tmp_path / "sales.csv"
    path.write_bytes(SALES.encode("utf-8"))
    return path


def _line(text, start):
    return next(line for line in text.splitlines() if line.startswith(start))


def _end(line, cell):
    return line.index(cell) + len(cell)


def test_values_and_totals(tmp_path):
    report = build_report(read_csv(_sales(tmp_path)), ["region"], MEASURES)
    assert [row[0] for row in report.rows] == ["East", "North", "West"]
    assert report.rows[0][-3:] == [Decimal("1500.50"), 2, Decimal("750.25")]
    assert report.rows[2][-3:] == [Decimal("-50.50"), 2, Decimal("-25.25")]
    assert report.totals[0] == "TOTAL"
    assert report.totals[-3:] == [Decimal("2450.00"), 5, Decimal("490")]
    assert report.row_count == 5


def test_plain_money_is_right_aligned(tmp_path):
    text = render_report(build_report(read_csv(_sales(tmp_path)), ["region"], MEASURES))
    east, north, west, total = (_line(text, key) for key in ("East", "North", "West", "TOTAL"))
    assert _end(east, "$1,500.50") == _end(north, "$1,000.00") == _end(west, "-$50.50") \
        == _end(total, "$2,450.00")
    assert _end(east, "$750.25") == _end(total, "$490.00") == len(east) == len(total)
    assert east.split()[-2] == "2" and total.split()[-2] == "5"
    assert text.splitlines()[-1] == "5 rows"


def test_markdown_alignment_row(tmp_path):
    report = build_report(read_csv(_sales(tmp_path)), ["region"], MEASURES)
    lines = render_report(report, "markdown").splitlines()
    rule = [cell.strip() for cell in lines[1].strip().strip("|").split("|")]
    assert [cell.endswith(":") for cell in rule] == [False, True, True, True]
    assert "| East " in lines[2] and "$1,500.50 |" in lines[2]


def test_cli_writes_report(tmp_path):
    out = tmp_path / "out.txt"
    assert main([str(_sales(tmp_path)), "-g", "region", "-m", "sum:amount", "-o", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert _line(text, "East").split()[-1] == "$1,500.50"
    assert _line(text, "TOTAL").split()[-1] == "$2,450.00"


def test_cli_where_and_dialect(tmp_path, capsys):
    path = tmp_path / "semi.csv"
    path.write_bytes("k;v\na;1.5\nb;2\na;7\n".encode("utf-8"))
    assert main([str(path), "--dialect", "semicolon", "-g", "k", "-m", "sum:v", "-w", "v<5"]) == 0
    out = capsys.readouterr().out
    assert _line(out, "a ").split()[-1] == "$1.50"
    assert _line(out, "TOTAL").split()[-1] == "$3.50"


def test_cli_error_exit(tmp_path, capsys):
    assert main([str(_sales(tmp_path)), "-g", "region", "-m", "sum:price"]) == 2
    assert capsys.readouterr().err == "tabreport: error: missing column: price\n"
