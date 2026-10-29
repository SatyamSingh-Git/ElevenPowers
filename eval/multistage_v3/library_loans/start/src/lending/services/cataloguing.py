"""Adding titles and copies to the catalogue, and withdrawing copies from stock."""
from .._generated import BRANCHES, MATERIALS
from ..errors import refuse
from ..model.catalogue import Copy, Title
from ..model.isbn import is_valid_isbn, normalise_isbn
from ..storage.catalogue_store import save_catalogue


def add_title(library, title, author, material, isbn=''):
    material = material.upper()
    isbn = normalise_isbn(isbn)
    if material not in MATERIALS:
        raise refuse('bad_catalogue', path='catalogue', problem=f'unknown material {material}')
    if not title.strip():
        raise refuse('bad_catalogue', path='catalogue', problem='a title needs a name')
    if isbn and not is_valid_isbn(isbn):
        raise refuse('bad_catalogue', path='catalogue', problem=f'invalid ISBN {isbn}')
    if isbn and library.catalogue.search(isbn):
        raise refuse('bad_catalogue', path='catalogue', problem=f'ISBN {isbn} is already catalogued')
    added = Title(library.catalogue.next_title_id(), title.strip(), author.strip(), material, isbn)
    library.catalogue.add_title(added)
    save_catalogue(library.directory, library.catalogue)
    return added


def add_copy(library, title_id, barcode, branch, price):
    title = library.catalogue.title(title_id.strip())
    barcode = barcode.strip()
    branch = branch.upper()
    if branch not in BRANCHES:
        raise refuse('bad_catalogue', path='catalogue', problem=f'unknown branch {branch}')
    if not barcode.isdigit():
        raise refuse('bad_catalogue', path='catalogue', problem=f'barcode {barcode} is not all digits')
    if any(copy.barcode == barcode for other in library.catalogue.titles() for copy in other.copies):
        raise refuse('bad_catalogue', path='catalogue', problem=f'barcode {barcode} is already in use')
    copy = Copy(barcode, title.id, branch, price)
    library.catalogue.add_copy(copy)
    save_catalogue(library.directory, library.catalogue)
    return copy


def withdraw(library, barcode):
    """Take a copy out of stock for good. Its past loans stay in the ledger."""
    copy = library.copy(barcode)
    if copy.barcode in library.loans:
        raise refuse('on_loan', barcode=copy.barcode)
    if any(hold.barcode == copy.barcode for hold in library.holds):
        raise refuse('held_for_other', barcode=copy.barcode)
    library.catalogue.remove_copy(copy.barcode)
    library.lost.discard(copy.barcode)
    save_catalogue(library.directory, library.catalogue)
    return copy
