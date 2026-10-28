"""`parcelpost manifest` lists shipments in booking order."""
import csv

from parcelpost.cli.main import main


def test_manifest_command_keeps_booking_order(tmp_path, capsys):
    data = tmp_path / "data"
    numbers = []
    for minute, account in enumerate(("BOLT", "ACME", "BOLT", "ACME")):
        assert main(["--data-dir", str(data), "--now", f"2026-03-02T09:0{minute}", "book", "--account", account,
                     "--name", "Pat", "--address", "1 Any Street", "--town", "Leeds", "--to", "LS1 4AP",
                     "--weight", "1"]) == 0
        numbers.append(capsys.readouterr().out.split()[1])
    assert main(["--data-dir", str(data), "--now", "2026-03-02T12:00", "manifest"]) == 0
    with open(data / "manifests" / "manifest-2026-03-02.csv", newline="", encoding="utf-8") as handle:
        assert [row["tracking_number"] for row in csv.DictReader(handle)] == numbers
