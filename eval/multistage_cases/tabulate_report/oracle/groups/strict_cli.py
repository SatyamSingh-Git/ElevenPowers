from tabreport.cli import main


def _write(tmp_path, text):
    path = tmp_path / "data.csv"
    path.write_bytes(text.encode("utf-8"))
    return path


def test_typo_in_a_cell_stops_the_report(tmp_path, capsys):
    path = _write(tmp_path, 'k,v\na,1\nb,"12,34"\n')
    assert main([str(path), "-g", "k", "-m", "sum:v"]) == 2
    assert capsys.readouterr().err == "tabreport: error: misplaced thousands separator: '12,34'\n"


def test_typo_in_a_filter_value(tmp_path, capsys):
    path = _write(tmp_path, "k,v\na,1\n")
    assert main([str(path), "-g", "k", "-w", "v>1,00"]) == 2
    assert capsys.readouterr().err == "tabreport: error: misplaced thousands separator: '1,00'\n"


def test_grouped_amounts_still_total(tmp_path):
    path = _write(tmp_path, 'k,v\na,"12,345.50"\nb,"1,000"\na,5\n')
    out = tmp_path / "out.csv"
    assert main([str(path), "-g", "k", "-m", "sum:v", "-f", "markdown", "-o", str(out)]) == 0
    last = out.read_text(encoding="utf-8").splitlines()[-3]
    assert [cell.strip() for cell in last.strip().strip("|").split("|")] == ["TOTAL", "$13,350.50"]
