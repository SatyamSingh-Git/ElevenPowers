"""The members CSV file `lend export` writes, for the mailing house and for backups."""
import csv

from ..model.dates import format_date

COLUMNS = ('card', 'name', 'email', 'type', 'born', 'joined')


def write_members_csv(path, members):
    """Write `members` sorted by card; returns how many rows were written."""
    rows = sorted(members, key=lambda member: member.card)
    with open(path, 'w', encoding='utf-8', newline='') as out:
        writer = csv.writer(out, lineterminator='\n')
        writer.writerow(COLUMNS)
        for member in rows:
            writer.writerow([member.card, member.name, member.email, member.kind,
                             format_date(member.born), format_date(member.joined)])
    return len(rows)
