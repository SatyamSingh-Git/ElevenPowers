"""Numbers printed by `parcelpost book` carry the S10 check digit."""
import re

from parcelpost.cli.main import main

WEIGHTS = (8, 6, 4, 2, 3, 5, 9, 7)


def s10_check(serial):
    check = 11 - sum(int(digit) * weight for digit, weight in zip(serial, WEIGHTS)) % 11
    return {10: 0, 11: 5}.get(check, check)


def test_book_prints_s10_numbers(tmp_path, capsys):
    base = ["--data-dir", str(tmp_path / "data"), "--now", "2026-03-02T09:00"]
    for _ in range(4):
        assert main([*base, "book", "--account", "BOLT", "--name", "Pat", "--address", "1 Any Street",
                     "--town", "Leeds", "--to", "LS1 4AP", "--weight", "1"]) == 0
        number = capsys.readouterr().out.split()[1]
        match = re.fullmatch(r"PP(\d{8})(\d)GB", number)
        assert match, number
        assert int(match.group(2)) == s10_check(match.group(1)), number
