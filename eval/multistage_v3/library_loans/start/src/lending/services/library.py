"""One library directory, loaded: settings, catalogue, members, holds and the ledger."""
from pathlib import Path

from ..config import load_settings
from ..errors import refuse
from ..model.calendar import Calendar
from ..model.dates import FixedClock
from ..model.loans import Loan
from ..model.members import normalise_card
from ..storage.catalogue_store import load_catalogue
from ..storage.holds_store import load_holds, save_holds
from ..storage.holidays_store import load_holidays
from ..storage.ledger import FILE as LEDGER_FILE, Ledger
from ..storage.members_store import load_members, save_members
from ..storage.transit_store import load_transit


class Library:
    def __init__(self, directory, clock, branch=None):
        self.directory = Path(directory)
        self.clock = clock
        self.branch = branch
        self.settings = load_settings(self.directory)
        self.calendar = Calendar(self.settings.closed_days, load_holidays(self.directory))
        self.catalogue = load_catalogue(self.directory)
        self.members = load_members(self.directory)
        self.holds = load_holds(self.directory)
        self.ledger = Ledger(self.directory / LEDGER_FILE)
        self.loans, self.lost = replay(self.ledger.entries())
        self.transit = load_transit(self.directory)

    @classmethod
    def open(cls, directory, today, branch=None):
        return cls(directory, FixedClock(today), branch)

    def today(self):
        return self.clock.today()

    def member(self, card):
        card = normalise_card(card)
        try:
            return self.members[card]
        except KeyError:
            raise refuse('unknown_member', card=card) from None

    def copy(self, barcode):
        return self.catalogue.copy(barcode.strip())

    def loan(self, barcode):
        try:
            return self.loans[barcode]
        except KeyError:
            raise refuse('not_on_loan', barcode=barcode) from None

    def loans_of(self, card):
        return sorted((loan for loan in self.loans.values() if loan.card == card),
                      key=lambda loan: (loan.due, loan.barcode))

    def holds_of(self, card):
        return [hold for hold in self.holds if hold.card == card]

    def is_free(self, barcode):
        """On the shelf for anyone: not out, not written off, not travelling and not set aside for a hold."""
        return (barcode not in self.loans and barcode not in self.lost and barcode not in self.transit
                and not any(hold.barcode == barcode for hold in self.holds))

    def record(self, entry):
        self.ledger.append(entry)

    def save_holds(self):
        save_holds(self.directory, self.holds)

    def save_members(self):
        save_members(self.directory, self.members)


def replay(entries):
    """The loans still out, and the copies written off, once every entry has taken effect in order.

    A written-off copy that turns up and is lent again is no longer lost.
    """
    loans, lost = {}, set()
    for entry in entries:
        if entry.event == 'checkout':
            loans[entry.barcode] = Loan(entry.barcode, entry.card, entry.date, entry.due)
            lost.discard(entry.barcode)
        elif entry.event == 'renew':
            loans[entry.barcode].due = entry.due
            loans[entry.barcode].renewals += 1
        elif entry.event == 'return':
            del loans[entry.barcode]
        elif entry.event == 'lost':
            del loans[entry.barcode]
            lost.add(entry.barcode)
    return loans, lost
