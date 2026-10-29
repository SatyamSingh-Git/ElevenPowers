"""Errors raised while reading and analysing surveys, and problems found in answers."""
from dataclasses import dataclass


class SurveyError(Exception):
    """A questionnaire is not well formed."""


class SurveyFileError(SurveyError):
    """A survey file cannot be read."""


class ResponseFileError(Exception):
    """A response file cannot be read. Rows count the header as row 1, as a spreadsheet does."""

    def __init__(self, row, message):
        super().__init__(f'row {row}: {message}')
        self.row = row
        self.message = message


class ProjectError(Exception):
    """A project folder is missing or already exists."""


class ConfigError(Exception):
    """A project's settings file holds a value that cannot be used."""


class WeightingError(Exception):
    """Weights cannot be read, computed or applied."""


class ScoringError(Exception):
    """A score cannot be computed."""


@dataclass(frozen=True)
class Issue:
    """One problem with one response."""

    respondent: str
    question: str
    message: str

    def __str__(self):
        return f'{self.respondent}: {self.message}'
