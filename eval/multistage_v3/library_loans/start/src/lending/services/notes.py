"""Staff notes on member accounts: lost cards, agreed payment plans, access needs."""
from ..errors import refuse
from ..storage.notes_store import load_notes, save_notes

LONGEST = 200


def add_note(library, card, text):
    member = library.member(card)
    text = ' '.join(text.split())
    if not text:
        raise refuse('bad_note', problem='a note needs some text')
    if len(text) > LONGEST:
        raise refuse('bad_note', problem=f'notes are limited to {LONGEST} characters')
    notes = load_notes(library.directory)
    notes.setdefault(member.card, []).append((library.today(), text))
    save_notes(library.directory, notes)
    return len(notes[member.card])


def notes_for(library, card):
    member = library.member(card)
    return load_notes(library.directory).get(member.card, [])


def clear_notes(library, card):
    member = library.member(card)
    notes = load_notes(library.directory)
    removed = len(notes.pop(member.card, []))
    save_notes(library.directory, notes)
    return removed
