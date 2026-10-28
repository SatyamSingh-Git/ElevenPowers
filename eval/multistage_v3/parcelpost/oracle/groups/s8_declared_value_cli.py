"""The command line quotes and books a 4000.00 declared value."""
from parcelpost.cli.main import main


def test_declared_value_on_the_command_line(tmp_path, capsys):
    base = ["--data-dir", str(tmp_path / "data"), "--now", "2026-03-02T09:00"]
    assert main([*base, "quote", "--to", "B1 1AA", "--weight", "1", "--value", "4000", "--service", "ground"]) == 0
    assert main([*base, "book", "--account", "ACME", "--name", "Pat", "--address", "1 Any Street",
                 "--town", "Birmingham", "--to", "B1 1AA", "--weight", "1", "--value", "4000.00"]) == 0
    capsys.readouterr()
    assert main([*base, "quote", "--to", "B1 1AA", "--weight", "1", "--value", "5000.01"]) == 1
    assert capsys.readouterr().err.strip() == "error: declared value 5000.01 is over the limit of 5000.00"
