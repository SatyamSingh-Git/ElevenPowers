"""Checks on the patient details reception types in."""
import re

from ..errors import ValidationError

NAME_LIMIT = 60
# UK numbers as patients give them: eleven digits starting with 0.
PHONE = re.compile(r"0\d{10}")


def check_name(name):
    """The name with runs of whitespace collapsed."""
    name = " ".join(name.split())
    if not name:
        raise ValidationError("patient name is required")
    if len(name) > NAME_LIMIT:
        raise ValidationError(f"patient name is longer than {NAME_LIMIT} characters")
    return name


def check_phone(phone):
    phone = phone.strip()
    if not PHONE.fullmatch(phone):
        raise ValidationError("invalid phone number")
    return phone
