"""`parcelpost report stalled` flags a shipment after 24 hours without a scan by default."""
from parcelpost.cli.main import main


def test_stalled_report_uses_the_new_default(tmp_path, capsys):
    data = str(tmp_path / "data")
    assert main(["--data-dir", data, "--now", "2026-03-02T09:00", "book", "--account", "ACME", "--name", "Pat",
                 "--address", "1 Any Street", "--town", "London", "--to", "SW1A 1AA", "--weight", "1"]) == 0
    number = capsys.readouterr().out.split()[1]
    assert main(["--data-dir", data, "--now", "2026-03-02T12:00", "manifest"]) == 0
    scans = tmp_path / "scans.csv"
    scans.write_text(f"tracking_number,code,date,time,depot\n{number},PU,2026-03-02,18:00,BHX\n", encoding="utf-8")
    assert main(["--data-dir", data, "--now", "2026-03-02T19:00", "scan", str(scans)]) == 0
    capsys.readouterr()

    assert main(["--data-dir", data, "--now", "2026-03-03T12:00", "report", "stalled"]) == 0
    assert number not in capsys.readouterr().out
    assert main(["--data-dir", data, "--now", "2026-03-04T00:00", "report", "stalled"]) == 0
    assert number in capsys.readouterr().out
