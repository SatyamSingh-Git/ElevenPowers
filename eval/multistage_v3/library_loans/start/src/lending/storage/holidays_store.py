"""holidays.txt: dates the library is closed, one YYYY-MM-DD per line.

Blank lines and lines starting with '#' are ignored, so the file can carry
notes such as the name of each holiday.
"""
from ..errors import LendingError, refuse
from ..model.dates import parse_date

FILE = 'holidays.txt'


def load_holidays(directory):
    path = directory / FILE
    if not path.exists():
        return set()
    days = set()
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        text = line.split('#', 1)[0].strip()
        if not text:
            continue
        try:
            days.add(parse_date(text))
        except LendingError as error:
            raise refuse('bad_calendar', path=FILE, line=number, problem=error.message) from None
    return days
