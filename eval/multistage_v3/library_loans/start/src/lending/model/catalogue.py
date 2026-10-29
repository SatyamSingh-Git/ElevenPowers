"""Titles and the physical copies the library owns of them."""
from dataclasses import dataclass, field

from ..errors import refuse
from .isbn import is_valid_isbn, normalise_isbn, to_isbn13


@dataclass
class Copy:
    barcode: str
    title_id: str
    branch: str
    price: int


@dataclass
class Title:
    id: str
    title: str
    author: str
    material: str
    isbn: str = ''
    copies: list = field(default_factory=list)


class Catalogue:
    def __init__(self, titles):
        self._titles = {title.id: title for title in titles}
        self._copies = {copy.barcode: copy for title in titles for copy in title.copies}

    def titles(self):
        return list(self._titles.values())

    def title(self, title_id):
        try:
            return self._titles[title_id]
        except KeyError:
            raise refuse('unknown_title', title=title_id) from None

    def copy(self, barcode):
        try:
            return self._copies[barcode]
        except KeyError:
            raise refuse('unknown_copy', barcode=barcode) from None

    def add_title(self, title):
        self._titles[title.id] = title

    def add_copy(self, copy):
        self._titles[copy.title_id].copies.append(copy)
        self._copies[copy.barcode] = copy

    def remove_copy(self, barcode):
        copy = self._copies.pop(barcode)
        self._titles[copy.title_id].copies.remove(copy)
        return copy

    def next_title_id(self):
        numbers = [int(title_id[1:]) for title_id in self._titles if title_id[1:].isdigit()]
        return f'T{max(numbers, default=0) + 1:04d}'

    def title_of(self, barcode):
        return self._titles[self.copy(barcode).title_id]

    def material_of(self, barcode):
        return self.title_of(barcode).material

    def search(self, text):
        """Titles whose title or author contains every word of `text`, alphabetically.

        Text that is a valid ISBN finds the title with that ISBN instead, in either form.
        """
        code = normalise_isbn(text)
        if is_valid_isbn(code):
            return [title for title in self._titles.values() if title.isbn and to_isbn13(title.isbn) == to_isbn13(code)]
        words = text.lower().split()
        found = [title for title in self._titles.values()
                 if all(word in f'{title.title} {title.author}'.lower() for word in words)]
        return sorted(found, key=lambda title: (title.title.lower(), title.id))
