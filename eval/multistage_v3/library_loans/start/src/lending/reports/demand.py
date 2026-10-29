"""Where demand outstrips stock: titles with members queueing, for the buying meeting."""
from .._generated import MATERIALS
from ..services.holds import waiting

COLUMNS = ('id', 'title', 'material', 'copies', 'waiting', 'per_copy')


def demand_rows(library, at_least=1):
    """Titles with at least `at_least` members waiting, the longest queue per copy first.

    Copies written off do not count as stock; a title with none left shows its
    whole queue as the ratio.
    """
    rows = []
    for title in library.catalogue.titles():
        queue = len(waiting(library, title.id))
        if queue < at_least:
            continue
        stock = sum(copy.barcode not in library.lost for copy in title.copies)
        ratio = queue / stock if stock else float(queue)
        rows.append({'id': title.id, 'title': title.title, 'material': MATERIALS[title.material],
                     'copies': stock, 'waiting': queue, 'per_copy': f'{ratio:.1f}'})
    rows.sort(key=lambda row: (-float(row['per_copy']), -row['waiting'], row['id']))
    return rows
