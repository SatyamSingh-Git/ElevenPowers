"""catalogue.json: every title and the copies of it, kept by the cataloguing team.

    {"titles": [{"id": "T0001", "title": "...", "author": "...", "material": "BK", "isbn": "9780261103344",
                 "copies": [{"barcode": "31000001", "branch": "CEN", "price": "12.99"}]}]}

The ISBN is optional; when present it must carry a valid check digit.
"""
import json

from .._generated import BRANCHES, MATERIALS
from ..errors import LendingError, refuse
from ..model.catalogue import Catalogue, Copy, Title
from ..model.isbn import is_valid_isbn, normalise_isbn
from ..model.money import parse_money, plain_amount

FILE = 'catalogue.json'


def load_catalogue(directory):
    path = directory / FILE
    if not path.exists():
        return Catalogue([])
    try:
        raw = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as error:
        raise refuse('bad_catalogue', path=FILE, problem=f'not JSON ({error.msg})') from None
    titles, barcodes = [], set()
    for record in raw.get('titles', []):
        title = _title(record)
        for copy in title.copies:
            if copy.barcode in barcodes:
                raise refuse('bad_catalogue', path=FILE, problem=f'barcode {copy.barcode} appears twice')
            barcodes.add(copy.barcode)
        titles.append(title)
    return Catalogue(titles)


def _title(record):
    try:
        title = Title(record['id'], record['title'], record.get('author', ''), record['material'],
                      normalise_isbn(record.get('isbn', '')))
        if title.material not in MATERIALS:
            raise refuse('bad_catalogue', path=FILE, problem=f'{title.id} has unknown material {title.material}')
        if title.isbn and not is_valid_isbn(title.isbn):
            raise refuse('bad_catalogue', path=FILE, problem=f'{title.id} has an invalid ISBN {title.isbn}')
        for raw in record.get('copies', []):
            if raw['branch'] not in BRANCHES:
                raise refuse('bad_catalogue', path=FILE, problem=f"{raw['barcode']} has unknown branch {raw['branch']}")
            title.copies.append(Copy(str(raw['barcode']), title.id, raw['branch'], parse_money(str(raw['price']))))
    except KeyError as missing:
        raise refuse('bad_catalogue', path=FILE, problem=f'a record has no {missing.args[0]}') from None
    except LendingError as error:
        if error.code == 'bad_catalogue':
            raise
        raise refuse('bad_catalogue', path=FILE, problem=error.message) from None
    return title


def save_catalogue(directory, catalogue):
    records = []
    for title in sorted(catalogue.titles(), key=lambda title: title.id):
        record = {'id': title.id, 'title': title.title, 'author': title.author, 'material': title.material}
        if title.isbn:
            record['isbn'] = title.isbn
        record['copies'] = [{'barcode': copy.barcode, 'branch': copy.branch, 'price': plain_amount(copy.price)}
                            for copy in title.copies]
        records.append(record)
    (directory / FILE).write_text(json.dumps({'titles': records}, indent=2) + '\n', encoding='utf-8')
