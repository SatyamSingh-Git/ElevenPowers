"""Working out a statement's layout from its header row."""
from ..errors import StatementError
from .base import header_of
from .registry import all_layouts


def detect_layout(text):
    header = set(header_of(text))
    candidates = [layout for layout in all_layouts() if set(layout.columns) <= header]
    if not candidates:
        raise StatementError("could not recognise the statement layout; use --layout")
    # A layout that needs more of the header's columns is the more specific match.
    return max(candidates, key=lambda layout: len(layout.columns))
