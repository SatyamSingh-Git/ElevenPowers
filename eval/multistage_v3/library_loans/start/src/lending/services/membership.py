"""Joining the library, keeping member details up to date, and moving member lists as CSV."""
from dataclasses import replace

from ..errors import refuse
from ..model.members import Member, normalise_card, problems
from ..storage.member_export import write_members_csv
from ..storage.member_import import read_members_csv
from .fines import balance

ADULT_AGE = 18


def add_member(library, card, name, email, kind, born):
    member = Member(normalise_card(card), name.strip(), email.strip(), kind, born, library.today())
    _check(member)
    if member.card in library.members:
        raise refuse('duplicate_member', card=member.card)
    library.members[member.card] = member
    library.save_members()
    return member


def update_member(library, card, name=None, email=None):
    member = library.member(card)
    changed = replace(member, name=member.name if name is None else name.strip(),
                      email=member.email if email is None else email.strip())
    _check(changed)
    library.members[member.card] = changed
    library.save_members()
    return changed


def leave(library, card):
    """Close a membership; only once everything is back and nothing is owed."""
    member = library.member(card)
    if library.loans_of(member.card):
        raise refuse('cannot_leave', card=member.card, reason='items are still on loan')
    if balance(library, member.card) > 0:
        raise refuse('cannot_leave', card=member.card, reason='money is still owed')
    library.holds = [hold for hold in library.holds if hold.card != member.card]
    del library.members[member.card]
    library.save_holds()
    library.save_members()
    return member


def promote_adults(library):
    """Child members who have turned 18 become adult members."""
    today = library.today()
    grown = [member for member in library.members.values()
             if member.kind == 'child' and _age(member.born, today) >= ADULT_AGE]
    for member in grown:
        library.members[member.card] = replace(member, kind='adult')
    if grown:
        library.save_members()
    return [member.card for member in grown]


def import_members(library, path):
    """Add every member in the CSV file; a card already registered stops the import before anything is saved."""
    incoming = read_members_csv(path)
    seen = set()
    for member in incoming:
        if member.card in library.members or member.card in seen:
            raise refuse('duplicate_member', card=member.card)
        seen.add(member.card)
    for member in incoming:
        library.members[member.card] = member
    library.save_members()
    return len(incoming)


def export_members(library, path):
    return write_members_csv(path, library.members.values())


def _check(member):
    found = problems(member)
    if found:
        raise refuse('invalid_member', card=member.card, problem='; '.join(found))


def _age(born, day):
    return day.year - born.year - ((day.month, day.day) < (born.month, born.day))
