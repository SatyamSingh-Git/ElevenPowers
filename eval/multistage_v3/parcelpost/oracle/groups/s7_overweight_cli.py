"""A 27 kg parcel to zone 1 by ground costs 12.90 + 18.00 + 7.5% fuel = 33.22."""
from parcelpost.cli.main import main


def test_quote_total_for_a_heavy_parcel(tmp_path, capsys):
    code = main(["--data-dir", str(tmp_path / "data"), "--now", "2026-03-02T09:00", "quote", "--to", "B1 1AA",
                 "--weight", "27", "--size", "40x30x30", "--service", "ground"])
    assert code == 0
    assert "33.22" in capsys.readouterr().out
