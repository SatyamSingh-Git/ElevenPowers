"""The command line quotes and books 30 kg and refuses 30.5 kg with the new message."""
from parcelpost.cli.main import main


def test_thirty_kilograms_on_the_command_line(tmp_path, capsys):
    base = ["--data-dir", str(tmp_path / "data"), "--now", "2026-03-02T09:00"]
    assert main([*base, "quote", "--to", "B1 1AA", "--weight", "30", "--size", "40x30x30", "--service", "ground"]) == 0
    assert main([*base, "book", "--account", "ACME", "--name", "Pat", "--address", "1 Any Street",
                 "--town", "Birmingham", "--to", "B1 1AA", "--weight", "30", "--size", "40x30x30"]) == 0
    capsys.readouterr()
    assert main([*base, "quote", "--to", "B1 1AA", "--weight", "30.5", "--service", "ground"]) == 1
    assert capsys.readouterr().err.strip() == "error: parcel over the 30 kg limit: 30.5 kg"
