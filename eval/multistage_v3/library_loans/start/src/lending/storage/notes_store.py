"""notes.json: short notes staff leave on a member's account, newest last.

    {"M1001": [{"date": "2026-03-02", "text": "Lost card, new one issued"}]}
"""
import json

from ..model.dates import format_date, parse_date

FILE = 'notes.json'


def load_notes(directory):
    path = directory / FILE
    if not path.exists():
        return {}
    return {card: [(parse_date(note['date']), note['text']) for note in notes]
            for card, notes in json.loads(path.read_text(encoding='utf-8')).items()}


def save_notes(directory, notes):
    records = {card: [{'date': format_date(day), 'text': text} for day, text in entries]
               for card, entries in sorted(notes.items()) if entries}
    (directory / FILE).write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
