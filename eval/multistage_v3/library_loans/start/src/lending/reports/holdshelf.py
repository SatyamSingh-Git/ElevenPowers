"""The hold shelf and the queues behind it."""
from ..model.dates import format_date
from ..model.holds import READY
from ..services.holds import collect_by, position, waiting

SHELF_COLUMNS = ('barcode', 'title', 'card', 'ready_on', 'collect_by')
QUEUE_COLUMNS = ('position', 'card', 'placed', 'status')


def shelf_rows(library):
    """Copies set aside for members, oldest first, so lapsed ones are easy to find."""
    ready = sorted((hold for hold in library.holds if hold.status == READY),
                   key=lambda hold: (hold.ready_on, hold.barcode))
    return [{'barcode': hold.barcode, 'title': library.catalogue.title(hold.title_id).title,
             'card': hold.card, 'ready_on': format_date(hold.ready_on),
             'collect_by': format_date(collect_by(library, hold))} for hold in ready]


def queue_rows(library, title_id):
    title = library.catalogue.title(title_id.strip())
    ready = [hold for hold in library.holds if hold.title_id == title.id and hold.status == READY]
    return [{'position': position(library, hold), 'card': hold.card, 'placed': format_date(hold.placed),
             'status': hold.status} for hold in ready + waiting(library, title.id)]
