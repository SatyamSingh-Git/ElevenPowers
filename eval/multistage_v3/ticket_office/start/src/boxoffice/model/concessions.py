"""Concession types, and what each takes off the face value of a seat."""
from ..errors import BoxOfficeError

# Percent off the face value of the seat's price tier.
CONCESSIONS = {
    "adult": 0,
    "child": 50,
    "senior": 20,
    "student": 25,
}


def concession_price(face, name):
    """The price of a seat with face value `face` sold at concession `name`, in pence.

    The discount is rounded to the nearest penny, halves up.
    """
    try:
        percent = CONCESSIONS[name]
    except KeyError:
        raise BoxOfficeError("unknown-concession", name=name) from None
    return face - (face * percent + 50) // 100
