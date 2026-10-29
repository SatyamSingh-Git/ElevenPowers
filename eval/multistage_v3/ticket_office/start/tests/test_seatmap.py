import pytest

from boxoffice.errors import BoxOfficeError
from boxoffice.storage.seatmap_format import format_seatmap, parse_seatmap

from conftest import SEATMAP


def test_parse():
    venue = parse_seatmap(SEATMAP)
    assert venue.name == "Test Hall"
    assert [section.name for section in venue.sections] == ["Stalls", "Circle"]
    assert venue.capacity == 16
    assert venue.seat("B6").flags == {"W"}
    assert venue.seat("C1").tier == "B"
    assert venue.tiers() == ["A", "B"]


def test_round_trip():
    assert format_seatmap(parse_seatmap(SEATMAP)) == SEATMAP


@pytest.mark.parametrize("text, problem", [
    ("section Stalls tier=A\n", "seat map line 1: section before venue"),
    ("venue X\nrow A 1-4\n", "seat map line 2: row before any section"),
    ("venue X\nsection S tier=A\nrow A 4-1\n", "seat map line 3: bad seat range 4-1"),
    ("venue X\nsection S tier=A\nrow A 1-4 Q:1\n", "seat map line 3: unknown access code Q:1"),
    ("venue X\nsection S tier=A\nrow A 1-4\nrow A 1-2\n", "seat map line 4: row A defined twice"),
    ("venue X\n", "seat map line 0: no seats"),
])
def test_problems(text, problem):
    with pytest.raises(BoxOfficeError) as raised:
        parse_seatmap(text)
    assert str(raised.value) == problem
