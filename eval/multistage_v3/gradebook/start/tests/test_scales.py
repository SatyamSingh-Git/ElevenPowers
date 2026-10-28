import pytest

from gradebook.errors import UnknownScale
from gradebook.grading.scales import get_scale


@pytest.mark.parametrize("percent, letter", [
    (100, "A"), (93.0, "A"), (92.9, "A-"), (90, "A-"), (87, "B+"), (79.9, "C+"),
    (60, "D-"), (59.9, "F"), (0, "F"),
])
def test_standard_scale(percent, letter):
    assert get_scale("standard").letter_for(percent) == letter


def test_pass_fail_scale():
    scale = get_scale("pass_fail")
    assert scale.letter_for(60) == "P"
    assert scale.letter_for(59.9) == "NP"


def test_minimum_of_a_letter():
    assert get_scale("standard").minimum("B") == 83.0


def test_unknown_scale():
    with pytest.raises(UnknownScale):
        get_scale("stars")
