"""Class statistics over a set of course grades."""
from dataclasses import dataclass

from ..grading.rounding import exact, round_half_up


@dataclass(frozen=True)
class ClassStatistics:
    students: int
    graded: int
    mean: float | None
    median: float | None
    highest: float | None
    lowest: float | None
    letters: dict  # letter -> count, in the scale's order


def class_statistics(grades, scale, decimals):
    percents = sorted(grade.percent for grade in grades if grade.percent is not None)
    letters = {letter: 0 for letter in scale.letters()}
    for grade in grades:
        if grade.letter in letters:
            letters[grade.letter] += 1
    if not percents:
        return ClassStatistics(len(grades), 0, None, None, None, None, letters)
    mean = round_half_up(sum(exact(p) for p in percents) / len(percents), decimals)
    middle = len(percents) // 2
    if len(percents) % 2:
        median = percents[middle]
    else:
        median = round_half_up((exact(percents[middle - 1]) + exact(percents[middle])) / 2, decimals)
    return ClassStatistics(len(grades), len(percents), mean, median, percents[-1], percents[0], letters)
