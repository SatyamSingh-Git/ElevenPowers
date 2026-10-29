"""ISBNs as cataloguers type them: with or without hyphens, ten or thirteen digits."""


def normalise_isbn(text):
    return ''.join(text.split()).replace('-', '').upper()


def is_valid_isbn(code):
    """Whether a normalised ISBN-10 or ISBN-13 has the right check digit."""
    if len(code) == 10 and code[:9].isdigit() and (code[9].isdigit() or code[9] == 'X'):
        digits = [int(char) for char in code[:9]] + [10 if code[9] == 'X' else int(code[9])]
        return sum(weight * digit for weight, digit in zip(range(10, 0, -1), digits)) % 11 == 0
    if len(code) == 13 and code.isdigit():
        total = sum(int(char) * (3 if position % 2 else 1) for position, char in enumerate(code))
        return total % 10 == 0
    return False


def to_isbn13(code):
    """The thirteen-digit form of a valid ISBN, so both forms of one book compare equal."""
    if len(code) == 13:
        return code
    stem = '978' + code[:9]
    total = sum(int(char) * (3 if position % 2 else 1) for position, char in enumerate(stem))
    return stem + str((10 - total % 10) % 10)
