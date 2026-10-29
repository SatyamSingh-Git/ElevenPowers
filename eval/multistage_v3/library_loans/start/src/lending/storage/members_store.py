"""members.json: one record per member, kept sorted by card.

    [{"card": "M1001", "name": "...", "email": "...", "type": "adult",
      "born": "1990-04-02", "joined": "2020-01-15"}]
"""
import json

from ..model.dates import format_date, parse_date
from ..model.members import Member

FILE = 'members.json'


def load_members(directory):
    path = directory / FILE
    if not path.exists():
        return {}
    members = {}
    for record in json.loads(path.read_text(encoding='utf-8')):
        member = Member(record['card'], record['name'], record.get('email', ''), record['type'],
                        parse_date(record['born']), parse_date(record['joined']))
        members[member.card] = member
    return members


def save_members(directory, members):
    records = [{'card': member.card, 'name': member.name, 'email': member.email, 'type': member.kind,
                'born': format_date(member.born), 'joined': format_date(member.joined)}
               for member in sorted(members.values(), key=lambda member: member.card)]
    (directory / FILE).write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
