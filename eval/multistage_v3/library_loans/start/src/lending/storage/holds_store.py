"""holds.json: every open hold, in the order the holds were placed.

The order is the queue: for each title, the first waiting hold in the file is
the next to be served.
"""
import json

from ..model.dates import format_date, parse_date
from ..model.holds import Hold

FILE = 'holds.json'


def load_holds(directory):
    path = directory / FILE
    if not path.exists():
        return []
    return [Hold(record['title'], record['card'], parse_date(record['placed']), record['status'],
                 record.get('barcode'), parse_date(record['ready_on']) if record.get('ready_on') else None)
            for record in json.loads(path.read_text(encoding='utf-8'))]


def save_holds(directory, holds):
    records = []
    for hold in holds:
        record = {'title': hold.title_id, 'card': hold.card, 'placed': format_date(hold.placed),
                  'status': hold.status}
        if hold.barcode:
            record['barcode'] = hold.barcode
            record['ready_on'] = format_date(hold.ready_on)
        records.append(record)
    (directory / FILE).write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
