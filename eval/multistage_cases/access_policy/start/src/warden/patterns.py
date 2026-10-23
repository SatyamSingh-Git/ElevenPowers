"""Resource patterns: `/`-separated segments with `*` and `**` wildcards.

`*` inside a segment matches any run of characters within that segment, so
`*.csv` matches `q1.csv` and a bare `*` matches exactly one segment. A `**`
segment matches zero or more whole segments.
"""
import re

from .errors import PolicyError

SEPARATOR = "/"
ANY_DEPTH = "**"


def split_path(path):
    """Segments of a resource path; leading, trailing and doubled separators are ignored."""
    return [part for part in path.split(SEPARATOR) if part]


def normalize(path):
    return SEPARATOR.join(split_path(path))


def _segment_regex(segment):
    return re.compile("[^/]*".join(re.escape(piece) for piece in segment.split("*")))


def _reach(segments, parts, accepts):
    # Positions in `parts` that can be reached after consuming each pattern segment.
    reachable = {0}
    for segment in segments:
        if segment == ANY_DEPTH:
            reachable = set(range(min(reachable), len(parts) + 1))
        else:
            reachable = {i + 1 for i in reachable if i < len(parts) and accepts(segment, parts[i])}
        if not reachable:
            return False
    return len(parts) in reachable


def _segment_covers(mine, theirs):
    if theirs == ANY_DEPTH:
        return False
    if mine == theirs or mine == "*":
        return True
    return "*" not in theirs and _segment_regex(mine).fullmatch(theirs) is not None


class Pattern:
    def __init__(self, text):
        segments = split_path(text)
        if not segments or any(ANY_DEPTH in s and s != ANY_DEPTH for s in segments):
            raise PolicyError(f"bad pattern: {text}")
        self.text = text
        self.segments = tuple(segments)
        self._regexes = {s: _segment_regex(s) for s in segments if s != ANY_DEPTH}

    def __repr__(self):
        return f"Pattern({self.text!r})"

    def __eq__(self, other):
        return isinstance(other, Pattern) and self.segments == other.segments

    def __hash__(self):
        return hash(self.segments)

    def matches(self, resource):
        return _reach(self.segments, split_path(resource),
                      lambda segment, part: self._regexes[segment].fullmatch(part) is not None)

    def covers(self, other):
        """True when every resource `other` matches is matched by this pattern too."""
        return _reach(self.segments, other.segments, _segment_covers)
