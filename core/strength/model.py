"""Bounded metadata contract shared by language engines and human reports."""
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
import re

STATUSES = ('detected', 'undetected', 'invalid', 'timed_out', 'error', 'not_run')
LIMITATION = ('Undetected mutations are possible test gaps, including equivalent '
              'behavior; these observations do not prove correctness or change verification verdicts.')


def relative(path):
    if not isinstance(path, str) or not path or '\\' in path or ':' in path:
        raise ValueError('expected a repository-relative path')
    parts = PurePosixPath(path).parts
    if path.startswith('/') or any(p in ('.', '..', '.git', '.elevenpowers') for p in parts):
        raise ValueError('unsafe repository-relative path')
    return path


@dataclass(frozen=True)
class Observation:
    id: str
    path: str
    line: int
    operator: str
    status: str
    end_line: int | None = None
    relevance: str = 'legacy_whole_file'
    context: str = ''

    def __post_init__(self):
        relative(self.path)
        if self.status not in STATUSES or type(self.line) is not int or not 1 <= self.line <= 1000000:
            raise ValueError('invalid mutation observation')
        for value in (self.id, self.operator):
            if not isinstance(value, str) or not value or len(value) > 256 or re.search(r'[\x00-\x1f]', value):
                raise ValueError('invalid observation metadata')
        if self.end_line is None:
            object.__setattr__(self, 'end_line', self.line)
        if type(self.end_line) is not int or not self.line <= self.end_line <= 1000000:
            raise ValueError('invalid mutation range')
        if self.relevance not in ('legacy_whole_file', 'changed_lines', 'changed_function', 'deletion_context'):
            raise ValueError('invalid mutation relevance')
        if not isinstance(self.context, str) or len(self.context) > 256 or re.search(r'[\x00-\x1f]', self.context):
            raise ValueError('invalid mutation context')

    def json(self):
        return asdict(self)


def summary(items):
    counts = {status: sum(item.status == status for item in items) for status in STATUSES}
    counts['incomplete'] = counts['timed_out'] + counts['error'] + counts['not_run']
    return counts
