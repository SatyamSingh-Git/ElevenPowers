import pytest

from parcelpost.core.ids import new_tracking_number


def test_tracking_number_layout():
    number = new_tracking_number(1)
    assert number.startswith("PP00000001")
    assert number.endswith("GB")
    assert len(number) == 13


@pytest.mark.parametrize("sequence, number", [
    (1, "PP000000019GB"),
    (2, "PP000000028GB"),
    (12345678, "PP123456782GB"),
])
def test_known_tracking_numbers(sequence, number):
    assert new_tracking_number(sequence) == number


def test_sequence_must_fit_eight_digits():
    with pytest.raises(ValueError):
        new_tracking_number(100_000_000)
