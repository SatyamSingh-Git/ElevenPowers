"""Holds: members queueing for the next copy of a title.

A hold waits until a copy comes back. The returned copy is then put on the
hold shelf for the first member waiting, who has `hold_pickup_days` days to
collect it; after that the hold lapses and the copy goes to the next member.
"""
from ..errors import refuse
from ..model.dates import add_days
from ..model.holds import READY, WAITING, Hold


def waiting(library, title_id):
    """Holds still waiting for a copy of the title, first in the queue first."""
    return [hold for hold in library.holds if hold.title_id == title_id and hold.status == WAITING]


def shelf_hold(library, barcode):
    """The ready hold a copy has been put aside for, if any."""
    return next((hold for hold in library.holds if hold.status == READY and hold.barcode == barcode), None)


def place_hold(library, card, title_id):
    member = library.member(card)
    title = library.catalogue.title(title_id.strip())
    mine = library.holds_of(member.card)
    if any(hold.title_id == title.id for hold in mine):
        raise refuse('duplicate_hold', card=member.card, title=title.id)
    if len(mine) >= library.settings.max_holds:
        raise refuse('hold_limit', card=member.card, limit=library.settings.max_holds)
    hold = Hold(title.id, member.card, library.today())
    library.holds.append(hold)
    spare = _spare_copy(library, title)
    if spare is not None:
        _put_aside(library, hold, spare)
    library.save_holds()
    return hold


def position(library, hold):
    """1 for the next member to be served; 0 once a copy is waiting for them."""
    if hold.status == READY:
        return 0
    return waiting(library, hold.title_id).index(hold) + 1


def collect_by(library, hold):
    return add_days(hold.ready_on, library.settings.hold_pickup_days)


def copy_returned(library, barcode):
    """Put a returned copy aside for the next member waiting, if there is one."""
    title_id = library.catalogue.copy(barcode).title_id
    queue = waiting(library, title_id)
    if not queue:
        return None
    _put_aside(library, queue[0], barcode)
    library.save_holds()
    return queue[0]


def collected(library, hold):
    library.holds.remove(hold)
    library.save_holds()


def expire_holds(library):
    """Drop ready holds nobody collected in time; their copies go to the next in line."""
    today = library.today()
    lapsed = [hold for hold in library.holds if hold.status == READY and today > collect_by(library, hold)]
    for hold in lapsed:
        library.holds.remove(hold)
        queue = waiting(library, hold.title_id)
        if queue:
            _put_aside(library, queue[0], hold.barcode)
    if lapsed:
        library.save_holds()
    return lapsed


def _spare_copy(library, title):
    return next((copy.barcode for copy in title.copies if library.is_free(copy.barcode)), None)


def _put_aside(library, hold, barcode):
    hold.status = READY
    hold.barcode = barcode
    hold.ready_on = library.today()
