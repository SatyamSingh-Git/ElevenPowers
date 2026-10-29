"""Catalogue search with shelf availability."""
from .._generated import MATERIALS

COLUMNS = ('id', 'title', 'author', 'material', 'copies', 'available')


def search_rows(library, text):
    rows = []
    for title in library.catalogue.search(text):
        free = [copy for copy in title.copies if library.is_free(copy.barcode)]
        rows.append({'id': title.id, 'title': title.title, 'author': title.author,
                     'material': MATERIALS[title.material], 'copies': len(title.copies), 'available': len(free)})
    return rows
