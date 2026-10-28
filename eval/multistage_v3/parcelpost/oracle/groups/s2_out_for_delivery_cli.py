"""`parcelpost track` shows out_for_delivery and `list --status` accepts it."""
from parcelpost.cli.main import main


def test_track_and_list_out_for_delivery(tmp_path, capsys):
    base = ["--data-dir", str(tmp_path / "data"), "--now", "2026-03-02T09:00"]
    assert main([*base, "book", "--account", "ACME", "--name", "Pat", "--address", "1 Any Street",
                 "--town", "London", "--to", "SW1A 1AA", "--weight", "2"]) == 0
    number = capsys.readouterr().out.split()[1]
    assert main([*base, "manifest", "--day", "2026-03-02"]) == 0
    scans = tmp_path / "scans.csv"
    scans.write_text("tracking_number,code,date,time,depot\n"
                     f"{number},PU,2026-03-02,18:00,BHX\n{number},OFD,2026-03-04,07:10,LDN\n", encoding="utf-8")
    assert main([*base, "scan", str(scans)]) == 0
    capsys.readouterr()

    assert main([*base[:2], "--now", "2026-03-04T08:00", "track", number]) == 0
    assert "out_for_delivery" in capsys.readouterr().out.splitlines()[0]

    assert main([*base, "list", "--status", "out_for_delivery"]) == 0
    assert number in capsys.readouterr().out
