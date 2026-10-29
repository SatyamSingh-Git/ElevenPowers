"""Cleaning responses before analysis: repeat submissions and speeders."""
from dataclasses import dataclass, field


@dataclass
class Cleaned:
    kept: list
    duplicates: list = field(default_factory=list)
    speeders: list = field(default_factory=list)


def latest_per_respondent(responses):
    """One response per respondent: the latest submitted.

    Responses without a date count as older than any dated one; between equal
    dates the one later in the list wins. Returns the kept responses, in their
    original order, and the ones they replace.
    """
    latest = {}
    for response in responses:
        current = latest.get(response.respondent)
        if current is None or response.submitted >= current.submitted:
            latest[response.respondent] = response
    kept, duplicates = [], []
    for response in responses:
        if latest[response.respondent] is response:
            kept.append(response)
        else:
            duplicates.append(response)
    return kept, duplicates


def split_speeders(responses, min_seconds):
    """Responses completed in fewer than `min_seconds` are speeders; 0 keeps everyone."""
    if not min_seconds:
        return list(responses), []
    kept, speeders = [], []
    for response in responses:
        if response.duration is not None and response.duration < min_seconds:
            speeders.append(response)
        else:
            kept.append(response)
    return kept, speeders


def clean(responses, *, min_seconds=0, existing=()):
    """Merge new responses into `existing` ones, newest submission per respondent, then drop speeders."""
    kept, duplicates = latest_per_respondent([*existing, *responses])
    kept, speeders = split_speeders(kept, min_seconds)
    return Cleaned(kept, duplicates, speeders)
