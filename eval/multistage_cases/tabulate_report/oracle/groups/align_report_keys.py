from tabreport import build_report, render_report
from tabreport.cli import main

ROWS = [
    {"store": "7", "year": "2024", "amount": "10"},
    {"store": "0042", "year": "2023", "amount": "2.5"},
    {"store": "123", "year": "2024", "amount": "1,000"},
    {"store": "7", "year": "2023", "amount": "4"},
]


def _rule(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def test_numeric_looking_keys_are_left_aligned_in_plain():
    lines = render_report(build_report(ROWS, ["store"], ["sum:amount", "count"])).splitlines()
    body = lines[2:5]
    assert [line.split()[0] for line in body] == ["0042", "123", "7"]
    assert all(line.startswith(line.split()[0] + " ") for line in body)
    assert len({len(line) for line in body}) == 1


def test_markdown_keys_left_measures_right():
    report = build_report(ROWS, ["year", "store"], ["sum:amount", "mean:amount"])
    lines = render_report(report, "markdown").splitlines()
    assert [cell.endswith(":") for cell in _rule(lines[1])] == [False, False, True, True]


def test_profile_counts_right_aligned(tmp_path, capsys):
    path = tmp_path / "wide.csv"
    rows = "\n".join(f"s{i},{i if i % 7 else ''}" for i in range(12))
    path.write_bytes(f"store,amount\n{rows}\n".encode("utf-8"))
    assert main([str(path), "--profile"]) == 0
    lines = capsys.readouterr().out.splitlines()
    store = next(line for line in lines if line.startswith("store "))
    amount = next(line for line in lines if line.startswith("amount "))
    assert store.split()[1:] == ["text", "12", "0"]
    assert amount.split()[1:] == ["number", "10", "2"]
    assert len(store) == len(amount)
    assert store.index("12") == amount.index("10")
