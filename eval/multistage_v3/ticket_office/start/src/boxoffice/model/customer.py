"""Customers who have booked before, so the counter can find them again."""
from dataclasses import dataclass
import re

from ..errors import BoxOfficeError

EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


@dataclass
class Customer:
    email: str
    name: str
    phone: str = ""
    mailing_list: bool = False

    def matches(self, text):
        """Whether `text` appears in the name, email or phone number, ignoring case."""
        text = text.strip().lower()
        if not text:
            return False
        return text in self.name.lower() or text in self.email or text in self.phone.replace(" ", "")

    def to_dict(self):
        return {"name": self.name, "phone": self.phone, "mailing_list": self.mailing_list}

    @classmethod
    def from_dict(cls, email, data):
        return cls(email, data["name"], data["phone"], data["mailing_list"])


def normalise_email(email):
    email = email.strip().lower()
    if not EMAIL.fullmatch(email):
        raise BoxOfficeError("bad-email", email=email)
    return email
