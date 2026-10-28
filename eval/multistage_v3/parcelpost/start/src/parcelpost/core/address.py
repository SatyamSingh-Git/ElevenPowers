"""Recipient addresses. Delivery is domestic only, so postcodes are UK style."""
from dataclasses import dataclass
import re

from .errors import ValidationError

POSTCODE = re.compile(r"^([A-Z]{1,2})[0-9][A-Z0-9]? [0-9][A-Z]{2}$")
MAX_FIELD_LENGTH = 35


@dataclass(frozen=True)
class Address:
    name: str
    line1: str
    town: str
    postcode: str

    def lines(self):
        return [self.name, self.line1, self.town, self.postcode]


def normalise_postcode(text):
    compact = "".join(str(text).split()).upper()
    candidate = f"{compact[:-3]} {compact[-3:]}"
    if not POSTCODE.match(candidate):
        raise ValidationError(f"invalid postcode: {text}")
    return candidate


def postcode_area(postcode):
    return POSTCODE.match(postcode).group(1)


def make_address(name, line1, town, postcode):
    fields = {"name": name, "line1": line1, "town": town}
    for field, value in fields.items():
        if not value or not value.strip():
            raise ValidationError(f"{field} is required")
        if len(value.strip()) > MAX_FIELD_LENGTH:
            raise ValidationError(f"{field} is longer than {MAX_FIELD_LENGTH} characters")
    return Address(name.strip(), line1.strip(), town.strip(), normalise_postcode(postcode))
