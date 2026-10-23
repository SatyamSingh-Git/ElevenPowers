from tabreport import build_report, render_report
from tabreport.cli import main

ROWS = [{"k": "a", "v": "10"}] * 1204 + [{"k": "b", "v": "2,500"}]


def _cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def test_large_count_is_not_grouped():
    lines = render_report(build_report(ROWS, ["k"], ["count", "sum:v"]), "markdown").splitlines()
    assert _cells(lines[2]) == ["a", "1204", "$12,040.00"]
    assert _cells(lines[4]) == ["TOTAL", "1205", "$14,540.00"]


def test_plain_amounts_without_currency_are_not_grouped():
    text = render_report(build_report(ROWS, ["k"], ["sum:v", "max:v"], currency=None))
    lines = text.splitlines()
    assert lines[2].split() == ["a", "12040.00", "10.00"]
    assert lines[3].split() == ["b", "2500.00", "2500.00"]
    assert next(line for line in lines if line.startswith("TOTAL")).split() == ["TOTAL", "14540.00", "2500.00"]


def test_cli_and_profile_counts(tmp_path, capsys):
    path = tmp_path / "big.csv"
    path.write_bytes(("k,v\n" + "a,1\n" * 1500).encode("utf-8"))
    assert main([str(path), "-g", "k", "--currency", "none", "-m", "count", "-m", "sum:v"]) == 0
    out = capsys.readouterr().out
    assert next(line for line in out.splitlines() if line.startswith("a ")).split() == ["a", "1500", "1500.00"]
    assert main([str(path), "--profile"]) == 0
    out = capsys.readouterr().out
    assert next(line for line in out.splitlines() if line.startswith("v ")).split() == ["v", "number", "1500", "0"]
