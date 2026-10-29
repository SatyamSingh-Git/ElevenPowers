"""Copies returned at a branch they do not belong to travel home in the van.

A desk that knows its own branch (`lend --branch RIV ...`) sends such copies
into transit when they come back, unless a member is waiting for the title, in
which case the copy goes on the hold shelf where it is. The home branch
receives the copy off the van and it is back on the shelf.
"""
from ..errors import refuse
from ..model.dates import format_date
from ..storage.transit_store import save_transit

COLUMNS = ('barcode', 'title', 'from', 'to', 'sent')


def send_home(library, barcode):
    """Put a copy just returned at this desk into transit if it lives elsewhere; returns whether it was."""
    copy = library.copy(barcode)
    if library.branch is None or copy.branch == library.branch:
        return False
    library.transit[copy.barcode] = (library.branch, library.today())
    save_transit(library.directory, library.transit)
    return True


def receive(library, barcode):
    copy = library.copy(barcode)
    if copy.barcode not in library.transit:
        raise refuse('not_in_transit', barcode=copy.barcode)
    if library.branch is not None and copy.branch != library.branch:
        raise refuse('wrong_branch', barcode=copy.barcode, branch=copy.branch)
    del library.transit[copy.barcode]
    save_transit(library.directory, library.transit)
    return copy


def transit_rows(library):
    rows = []
    for barcode, (sender, sent) in sorted(library.transit.items(), key=lambda item: (item[1][1], item[0])):
        copy = library.copy(barcode)
        rows.append({'barcode': barcode, 'title': library.catalogue.title(copy.title_id).title,
                     'from': sender, 'to': copy.branch, 'sent': format_date(sent)})
    return rows
