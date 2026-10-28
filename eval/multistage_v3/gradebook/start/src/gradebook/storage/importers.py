"""The importer registry: `gradebook import <kind> <file>` looks the kind up here.

An importer is called as importer(book, path) and returns an ImportSummary.
It records through the book, so the book's own checks apply to every row.
"""
from dataclasses import dataclass

from ..errors import GradebookError, ImportFailed, UnknownImportKind

IMPORTERS = {}


@dataclass(frozen=True)
class ImportSummary:
    kind: str
    rows: int
    recorded: int
    skipped: int = 0


def importer(kind):
    def register(function):
        IMPORTERS[kind] = function
        return function
    return register


def get_importer(kind):
    try:
        return IMPORTERS[kind]
    except KeyError:
        raise UnknownImportKind(kind) from None


def at_line(line, action):
    """Run one row's action, putting the line number in front of any error it raises."""
    try:
        return action()
    except ImportFailed:
        raise
    except GradebookError as error:
        raise ImportFailed(f"line {line}: {error}") from None
