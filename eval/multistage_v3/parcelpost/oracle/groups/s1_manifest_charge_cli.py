"""The manifest written by `parcelpost manifest` carries charges as 0.00."""
import csv

from parcelpost.cli.main import main


def test_manifest_command_writes_pounds(tmp_path, capsys):
    data = tmp_path / "data"
    base = ["--data-dir", str(data), "--now", "2026-03-02T09:00"]
    totals = {}
    for account, postcode, weight in (("ACME", "SW1A 1AA", "2.5"), ("BOLT", "LS1 4AP", "4"), ("ACME", "B1 1AA", "1")):
        code = main([*base, "book", "--account", account, "--name", "Pat", "--address", "1 Any Street",
                     "--town", "Anytown", "--to", postcode, "--weight", weight])
        assert code == 0
        _, number, _, total = capsys.readouterr().out.splitlines()[0].split()
        totals[number] = total
    assert main([*base, "manifest", "--day", "2026-03-02"]) == 0
    with open(data / "manifests" / "manifest-2026-03-02.csv", newline="", encoding="utf-8") as handle:
        charges = {row["tracking_number"]: row["charge"] for row in csv.DictReader(handle)}
    assert charges == totals
