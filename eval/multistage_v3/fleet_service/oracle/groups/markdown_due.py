"""`--format markdown` prints the due list as a pipe table with the CSV's values."""
import csv
from datetime import date
import io
import re

import pytest

from fleetkeep.cli.main import main
from fleetkeep.clock import FixedClock


@pytest.fixture
def fk(tmp_path, capsys):
    root = tmp_path / "fleet"

    def fk(*args):
        code = main(["--fleet", str(root), *map(str, args)], clock=FixedClock(date(2026, 3, 1)))
        out, err = capsys.readouterr()
        assert code == 0, err
        return out

    fk("init", "--name", "North")
    fk("vehicle", "add", "VAN-111", "--class", "light", "--make", "Ford", "--model", "Transit",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    fk("odometer", "add", "VAN-111", "6300", "--on", "2026-02-20")
    return fk


def _cells(line):
    assert line.startswith("|") and line.endswith("|"), line
    return [cell.strip() for cell in line[1:-1].split("|")]


def test_pipe_table_matches_csv(fk):
    lines = fk("due", "--as-of", "2026-02-21", "--format", "markdown").strip().splitlines()
    expected = list(csv.reader(io.StringIO(fk("due", "--as-of", "2026-02-21", "--format", "csv"))))
    assert _cells(lines[0]) == expected[0]
    assert all(re.fullmatch(r":?-{3,}:?", cell) for cell in _cells(lines[1]))
    assert len(_cells(lines[1])) == len(expected[0])
    assert [_cells(line) for line in lines[2:]] == expected[1:]

