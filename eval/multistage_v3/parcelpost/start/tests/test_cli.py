import pytest

from parcelpost.cli.main import main

NOW = "2026-03-02T10:00"
RECIPIENT = ["--name", "Ann Example", "--address", "1 High Street", "--town", "London", "--to", "SW1A 1AA"]


@pytest.fixture
def run(tmp_path, capsys):
    def run(*argv, now=NOW):
        code = main(["--data-dir", str(tmp_path), "--now", now, *argv])
        captured = capsys.readouterr()
        return code, captured.out, captured.err
    return run


def test_quote_one_service(run):
    code, out, _ = run("quote", "--to", "sw1a1aa", "--weight", "2.5", "--service", "ground")
    assert code == 0
    assert out.splitlines()[0] == "Ground: zone 4, billable weight 2.5 kg, expected 2026-03-05"
    assert "Total" in out and "7.63" in out


def test_quote_every_service(run):
    code, out, _ = run("quote", "--to", "B1 1AA", "--weight", "1", "--residential")
    assert code == 0
    assert [line.split(":")[0] for line in out.splitlines() if "zone" in line] == ["Economy", "Ground", "Express"]
    assert "Residential delivery" in out


def test_book_list_and_track(run):
    code, out, _ = run("book", "--account", "acme", *RECIPIENT, "--weight", "2.5")
    assert code == 0
    assert out.splitlines()[0] == "booked PP000000019GB ground 7.63"
    _, out, _ = run("list", "--account", "ACME")
    assert "PP000000019GB" in out and "booked" in out
    code, out, _ = run("track", "pp000000019gb")
    assert code == 0
    assert out.splitlines()[0] == "PP000000019GB  booked"
    assert "No scans yet." in out


def test_book_from_a_saved_address(run):
    assert run("address", "add", "acme", "office", *RECIPIENT)[0] == 0
    code, out, _ = run("book", "--account", "ACME", "--recipient", "office", "--weight", "1")
    assert code == 0
    assert out.startswith("booked PP")


def test_book_needs_a_recipient(run):
    code, _, err = run("book", "--account", "ACME", "--weight", "1")
    assert code == 1
    assert "give --recipient" in err


def test_manifest_and_daily_report(run):
    run("book", "--account", "ACME", *RECIPIENT, "--weight", "2.5")
    code, out, _ = run("manifest")
    assert code == 0
    assert out.strip().endswith("with 1 shipments")
    _, out, _ = run("report", "daily", "--day", "2026-03-02")
    assert "Manifested" in out


def test_errors_and_exit_codes(run):
    code, _, err = run("track", "PP999999999GB")
    assert code == 3
    assert err.strip() == "error: no shipment PP999999999GB"
    code, _, err = run("quote", "--to", "JE2 3AB", "--weight", "1")
    assert code == 1
    assert err.strip() == "error: no service to postcode area JE"
    with pytest.raises(SystemExit) as raised:
        run("quote", "--weight", "1")
    assert raised.value.code == 2


def test_settings_and_zones(run):
    _, out, _ = run("settings")
    assert "stale_hours" in out
    _, out, _ = run("zones")
    assert out.splitlines()[0].startswith("zone 1: B CV")
