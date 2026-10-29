"""Reading members from CSV: the council's sign-up sheet, or a file `lend export` wrote.

The file needs a header row naming at least the columns card, name, email,
type, born and joined; other columns are ignored. Rows are checked as they are
read and the first bad row stops the import, so nothing is half-loaded.
"""
import csv
from datetime import date

from ..errors import refuse
from ..model.members import Member, normalise_card, problems

REQUIRED = ('card', 'name', 'email', 'type', 'born', 'joined')


def read_members_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        missing = [column for column in REQUIRED if column not in (reader.fieldnames or [])]
        if missing:
            raise refuse('bad_import', row=1, problem=f"missing columns {', '.join(missing)}")
        members = []
        for number, row in enumerate(reader, 2):
            member = Member(normalise_card(row['card']), row['name'].strip(), row['email'].strip(),
                            row['type'].strip().lower(), _day(row['born'], number), _day(row['joined'], number))
            found = problems(member)
            if found:
                raise refuse('bad_import', row=number, problem='; '.join(found))
            members.append(member)
    return members


def _day(text, number):
    try:
        return date.fromisoformat(text.strip())
    except ValueError:
        raise refuse('bad_import', row=number, problem=f'not a date: {text}') from None
