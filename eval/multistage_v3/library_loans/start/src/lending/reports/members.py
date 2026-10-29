"""Reports on members: who owes, who is active, how membership is made up."""
from ..model.dates import format_date
from ..model.members import KINDS
from ..model.money import format_money
from ..services.fines import balance
from ..services.history import spells

DEBTOR_COLUMNS = ('card', 'name', 'email', 'owes')
PROFILE_COLUMNS = ('type', 'members', 'active', 'joined_this_year')
HISTORY_COLUMNS = ('barcode', 'title', 'issued', 'ended', 'outcome', 'renewals')
LAPSED_COLUMNS = ('card', 'name', 'email', 'last_borrowed')


def debtor_rows(library, at_least=1):
    """Members owing at least `at_least` pence, largest debt first."""
    rows = []
    for member in library.members.values():
        owed = balance(library, member.card)
        if owed >= at_least:
            rows.append({'card': member.card, 'name': member.name, 'email': member.email, 'owes': owed})
    rows.sort(key=lambda row: (-row['owes'], row['card']))
    return [{**row, 'owes': format_money(row['owes'])} for row in rows]


def profile_rows(library, active_since):
    """Members by type; active means they borrowed something on or after `active_since`."""
    borrowers = {spell.card for spell in spells(library.ledger.entries()) if spell.issued >= active_since}
    year = library.today().year
    rows = []
    for kind in KINDS:
        members = [member for member in library.members.values() if member.kind == kind]
        rows.append({'type': kind, 'members': len(members),
                     'active': sum(member.card in borrowers for member in members),
                     'joined_this_year': sum(member.joined.year == year for member in members)})
    return rows


def history_rows(library, history):
    return [{'barcode': spell.barcode, 'title': library.catalogue.title_of(spell.barcode).title,
             'issued': format_date(spell.issued), 'ended': format_date(spell.ended) if spell.ended else '',
             'outcome': spell.outcome, 'renewals': spell.renewals} for spell in history]


def lapsed_rows(library, since):
    """Members who have borrowed nothing since `since`, for the "we miss you" mailing."""
    last = {}
    for spell in spells(library.ledger.entries()):
        last[spell.card] = max(spell.issued, last.get(spell.card, spell.issued))
    rows = []
    for member in sorted(library.members.values(), key=lambda member: member.card):
        borrowed = last.get(member.card)
        if member.joined < since and (borrowed is None or borrowed < since):
            rows.append({'card': member.card, 'name': member.name, 'email': member.email,
                         'last_borrowed': format_date(borrowed) if borrowed else 'never'})
    return rows
