"""Saved recipients, per account, so regular destinations are booked by a short alias."""
from dataclasses import asdict
import json
from pathlib import Path
import re

from ..core.address import Address
from ..core.errors import ValidationError
from .files import write_atomic

ALIAS = re.compile(r"^[a-z0-9][a-z0-9-]{0,19}$")


class AddressBook:
    def __init__(self, path):
        self.path = Path(path)
        self._entries = {}
        if self.path.is_file():
            document = json.loads(self.path.read_text(encoding="utf-8"))
            for account, saved in document["accounts"].items():
                self._entries[account] = {alias: Address(**fields) for alias, fields in saved.items()}

    def save_address(self, account, alias, address):
        if not ALIAS.match(alias):
            raise ValidationError(f"invalid alias: {alias} (lower-case letters, digits and hyphens)")
        self._entries.setdefault(account, {})[alias] = address

    def lookup(self, account, alias):
        try:
            return self._entries[account][alias]
        except KeyError:
            raise ValidationError(f"account {account} has no saved address {alias}") from None

    def aliases(self, account):
        return sorted(self._entries.get(account, {}).items())

    def save(self):
        document = {"accounts": {account: {alias: asdict(address) for alias, address in sorted(saved.items())}
                                 for account, saved in sorted(self._entries.items())}}
        write_atomic(self.path, json.dumps(document, indent=2) + "\n")
