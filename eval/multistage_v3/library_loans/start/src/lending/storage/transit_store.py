"""transit.json: copies on their way back to their home branch.

    {"31000004": {"from": "RIV", "sent": "2026-03-02"}}
"""
import json

from ..model.dates import format_date, parse_date

FILE = 'transit.json'


def load_transit(directory):
    path = directory / FILE
    if not path.exists():
        return {}
    return {barcode: (record['from'], parse_date(record['sent']))
            for barcode, record in json.loads(path.read_text(encoding='utf-8')).items()}


def save_transit(directory, transit):
    records = {barcode: {'from': branch, 'sent': format_date(sent)}
               for barcode, (branch, sent) in sorted(transit.items())}
    (directory / FILE).write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
