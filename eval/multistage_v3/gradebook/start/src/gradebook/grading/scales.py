"""Letter scales: which letter a final percent earns."""
from dataclasses import dataclass

from .._generated import STANDARD_THRESHOLDS
from ..errors import UnknownScale


@dataclass(frozen=True)
class LetterScale:
    name: str
    thresholds: tuple  # (minimum percent, letter), highest first

    def letter_for(self, percent):
        for minimum, letter in self.thresholds:
            if percent >= minimum:
                return letter
        return self.thresholds[-1][1]

    def letters(self):
        return [letter for _, letter in self.thresholds]

    def minimum(self, letter):
        for minimum, candidate in self.thresholds:
            if candidate == letter:
                return minimum
        raise KeyError(letter)


SCALES = {
    "standard": LetterScale("standard", STANDARD_THRESHOLDS),
    "pass_fail": LetterScale("pass_fail", ((60.0, "P"), (0.0, "NP"))),
}


def get_scale(name):
    try:
        return SCALES[name]
    except KeyError:
        raise UnknownScale(name) from None
