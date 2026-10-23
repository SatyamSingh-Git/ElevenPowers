from ledgerbook.cli import main


def _books(tmp_path):
    path = str(tmp_path / "books.jsonl")
    assert main([path, "init"]) == 0
    assert main([path, "open", "Assets:Cash", "Expenses:Food", "Equity:Opening"]) == 0
    assert main([path, "post", "2026-03-01", "Float", "Assets:Cash=300", "Equity:Opening"]) == 0
    assert main([path, "post", "2026-03-04", "Bakery", "Expenses:Food=4.20", "Assets:Cash"]) == 0
    assert main([path, "post", "2026-03-09", "Market", "Expenses:Food=31.75", "Assets:Cash"]) == 0
    assert main([path, "post", "2026-03-20", "Deli", "Expenses:Food=12", "Assets:Cash"]) == 0
    return path


def test_from_and_to(tmp_path, capsys):
    path = _books(tmp_path)
    capsys.readouterr()
    assert main([path, "statement", "Assets:Cash", "--from", "2026-03-04", "--to", "2026-03-09"]) == 0
    out = capsys.readouterr().out
    rows = [line for line in out.splitlines() if line[:4] == "2026"]
    assert len(rows) == 3
    assert rows[0].startswith("2026-03-04") and "Opening balance" in rows[0] and rows[0].rstrip().endswith("300.00")
    assert [row.split() for row in rows[1:]] == [
        ["2026-03-04", "Bakery", "-4.20", "295.80"],
        ["2026-03-09", "Market", "-31.75", "264.05"],
    ]


def test_to_alone(tmp_path, capsys):
    path = _books(tmp_path)
    capsys.readouterr()
    assert main([path, "statement", "Assets:Cash", "--to", "2026-03-04"]) == 0
    out = capsys.readouterr().out
    assert "Float" in out and "Bakery" in out
    assert "Market" not in out and "Opening balance" not in out
