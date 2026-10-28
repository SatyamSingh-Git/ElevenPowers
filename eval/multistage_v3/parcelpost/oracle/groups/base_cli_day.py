"""A full collection day through the `parcelpost` command line."""
from parcelpost.cli.main import main

BOOKINGS = [
    ["--account", "ACME", "--to", "SW1A 1AA", "--weight", "2.5"],
    ["--account", "BOLT", "--to", "LS1 4AP", "--weight", "27", "--size", "60x40x40", "--residential"],
    ["--account", "ACME", "--to", "G1 1AA", "--weight", "1", "--service", "express"],
    ["--account", "BOLT", "--to", "B1 1AA", "--weight", "1"],
]
RECIPIENT = ["--name", "Pat Recipient", "--address", "1 Any Street", "--town", "Anytown"]


def _run(tmp_path, capsys, *argv, now="2026-03-02T09:00"):
    code = main(["--data-dir", str(tmp_path / "data"), "--now", now, *argv])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_quote_a_heavy_parcel(tmp_path, capsys):
    code, out, _ = _run(tmp_path, capsys, "quote", "--to", "LS1 4AP", "--weight", "27", "--size", "60x40x40")
    assert code == 0
    assert "Total" in out


def test_collection_day(tmp_path, capsys):
    numbers = []
    for booking in BOOKINGS:
        code, out, _ = _run(tmp_path, capsys, "book", *booking, *RECIPIENT)
        assert code == 0
        numbers.append(out.split()[1])
    assert len(set(numbers)) == 4

    assert _run(tmp_path, capsys, "manifest", "--day", "2026-03-02")[0] == 0
    code, out, _ = _run(tmp_path, capsys, "bill", "--day", "2026-03-02")
    assert code == 0
    assert out.count("INV-ACME-20260302") == 1
    assert out.count("INV-BOLT-20260302") == 1

    scans = tmp_path / "scans.csv"
    scans.write_text("tracking_number,code,date,time,depot\n"
                     + "".join(f"{number},PU,2026-03-02,18:00,BHX\n" for number in numbers)
                     + f"{numbers[0]},OFD,2026-03-04,07:00,LDN\n"
                     + f"{numbers[2]},DL,2026-03-03,11:00,GLA\n", encoding="utf-8")
    code, out, _ = _run(tmp_path, capsys, "scan", str(scans))
    assert code == 0
    assert out.strip() == "recorded 6 scans for 4 shipments"

    code, out, _ = _run(tmp_path, capsys, "track", numbers[2], now="2026-03-04T12:00")
    assert code == 0
    assert "delivered" in out.splitlines()[0]

    code, out, _ = _run(tmp_path, capsys, "report", "daily", "--day", "2026-03-02")
    assert code == 0
    assert out.strip()
