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
    out = tmp_path / "out.txt"
    assert main([str(path), *options, "-o", str(out)]) == 0
    return out.read_text(encoding="utf-8")


def _cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def test_markdown_has_one_column_per_key(tmp_path):
    text = _run(tmp_path, "-g", "region,product", "-m", "sum:amount", "-f", "markdown")
    lines = [line for line in text.splitlines() if line.startswith("|")]
    assert _cells(lines[0])[:2] == ["region", "product"]
    assert len(_cells(lines[0])) == 3
    assert _cells(lines[2]) == ["East", "Gadget", "$300.00"]
    assert _cells(lines[5]) == ["West", "Gadget", "-$150.25"]
    assert _cells(lines[-1]) == ["TOTAL", "", "$2,450.00"]


def test_plain_header_names_the_key_column(tmp_path):
    text = _run(tmp_path, "-g", "product", "-m", "count")
    lines = text.splitlines()
    assert lines[0].split() == ["product", "count"]
    assert lines[2].split() == ["Gadget", "2"]
    assert lines[3].split() == ["Widget", "3"]
