from tabreport.cli import main


def test_report_to_file(sales, tmp_path):
    out = tmp_path / "out.md"
    assert main([str(sales), "-g", "region", "-m", "sum:amount", "-f", "markdown", "-o", str(out)]) == 0
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[2] == "| East  |   $1,500.50 |"
    assert lines[5] == "| TOTAL |   $2,450.00 |"


def test_report_to_stdout(sales, capsys):
    assert main([str(sales), "-g", "region", "--no-totals"]) == 0
    out = capsys.readouterr().out
    assert "TOTAL" not in out
    assert "North      1" in out


def test_where_filters_rows(sales, capsys):
    assert main([str(sales), "-g", "product", "-m", "sum:units", "-w", "amount>=100", "--currency", "none"]) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[2:4] == ["Gadget        2.00", "Widget        8.00"]
    assert out.endswith("\n3 rows\n")


def test_semicolon_dialect(write_csv, capsys):
    path = write_csv("k;v\na;1.5\na;2\n")
    assert main([str(path), "--dialect", "semicolon", "-g", "k", "-m", "sum:v", "--currency", "eur"]) == 0
    assert capsys.readouterr().out.splitlines()[2] == "a       €3.50"


def test_tab_delimiter(write_csv, capsys):
    path = write_csv("k\tv\na\t1\n")
    assert main([str(path), "--delimiter", "\\t", "-g", "k"]) == 0
    assert capsys.readouterr().out.splitlines()[2] == "a          1"


def test_errors_exit_2(sales, tmp_path, capsys):
    assert main([str(sales), "-g", "region", "-m", "sum:price"]) == 2
    assert capsys.readouterr().err == "tabreport: error: missing column: price\n"
    assert main([str(tmp_path / "nope.csv")]) == 2
    assert capsys.readouterr().err.startswith("tabreport: error: cannot read ")
    assert main([str(sales), "-w", "amount>lots"]) == 2
    assert capsys.readouterr().err == "tabreport: error: not a number: 'lots'\n"


def test_profile(sales, capsys):
    assert main([str(sales), "--profile"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "column   kind    filled  blank"
    assert lines[5] == "amount   number       5      0"
