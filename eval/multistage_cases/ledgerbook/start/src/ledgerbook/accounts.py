"""Accounts and the chart that holds them.

An account name is a path of capitalised segments joined by ":", and its first
segment fixes the account type: "Assets:Bank:Checking" is an asset.
"""
from dataclasses import dataclass
import re

from .errors import AccountError

SEPARATOR = ":"
ROOTS = {
    "Assets": "asset",
    "Liabilities": "liability",
    "Equity": "equity",
    "Income": "income",
    "Expenses": "expense",
}
DEBIT_NORMAL = frozenset({"asset", "expense"})

_SEGMENT = re.compile(r"[A-Z][A-Za-z0-9-]*")


@dataclass(frozen=True)
class Account:
    name: str
    type: str

    @property
    def debit_normal(self):
        """True for assets and expenses, which grow with debits."""
        return self.type in DEBIT_NORMAL

    @property
    def parent(self):
        return self.name.rpartition(SEPARATOR)[0]

    @property
    def leaf(self):
        return self.name.rpartition(SEPARATOR)[2]


def account_type(name):
    """The type `name` implies, or AccountError when the name is malformed."""
    segments = name.split(SEPARATOR)
    if len(segments) < 2 or segments[0] not in ROOTS or not all(_SEGMENT.fullmatch(s) for s in segments):
        raise AccountError(f"invalid account name: {name}")
    return ROOTS[segments[0]]


def is_under(name, prefix):
    """True when `name` is `prefix` itself or sits below it in the hierarchy."""
    return name == prefix or name.startswith(prefix + SEPARATOR)


class Chart:
    """The open accounts of one ledger, iterated in name order."""

    def __init__(self):
        self._accounts = {}

    def open(self, name):
        kind = account_type(name)
        if name in self._accounts:
            raise AccountError(f"account already open: {name}")
        account = Account(name, kind)
        self._accounts[name] = account
        return account

    def get(self, name):
        try:
            return self._accounts[name]
        except KeyError:
            raise AccountError(f"unknown account: {name}") from None

    def under(self, prefix):
        return [account for account in self if is_under(account.name, prefix)]

    def __contains__(self, name):
        return name in self._accounts

    def __iter__(self):
        return iter(sorted(self._accounts.values(), key=lambda account: account.name))

    def __len__(self):
        return len(self._accounts)
