"""Customer accounts: who is billed, where invoices go and how long they have to pay."""
from dataclasses import dataclass
import re

from .errors import ValidationError

ACCOUNT_CODE = re.compile(r"^[A-Z0-9]{2,10}$")
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
DEFAULT_PAYMENT_DAYS = 30
MAX_PAYMENT_DAYS = 90


@dataclass(frozen=True)
class Account:
    code: str
    name: str
    email: str
    payment_days: int = DEFAULT_PAYMENT_DAYS


def check_account_code(code):
    if not ACCOUNT_CODE.match(code):
        raise ValidationError(f"invalid account: {code} (2 to 10 capital letters or digits)")
    return code


def make_account(code, name, email, payment_days=DEFAULT_PAYMENT_DAYS):
    check_account_code(code)
    if not name.strip():
        raise ValidationError("account name is required")
    if not EMAIL.match(email.strip()):
        raise ValidationError(f"invalid email address: {email}")
    if not 0 < payment_days <= MAX_PAYMENT_DAYS:
        raise ValidationError(f"payment days must be between 1 and {MAX_PAYMENT_DAYS}")
    return Account(code, name.strip(), email.strip(), payment_days)
