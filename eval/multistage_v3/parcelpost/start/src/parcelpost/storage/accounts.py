"""The account book: registered customer accounts, kept in one JSON file."""
from dataclasses import asdict
import json
from pathlib import Path

from ..core.accounts import Account
from ..core.errors import ValidationError
from .files import write_atomic


class AccountBook:
    def __init__(self, path):
        self.path = Path(path)
        self._accounts = {}
        if self.path.is_file():
            for record in json.loads(self.path.read_text(encoding="utf-8"))["accounts"]:
                self._accounts[record["code"]] = Account(**record)

    def add(self, account):
        if account.code in self._accounts:
            raise ValidationError(f"account {account.code} already exists")
        self._accounts[account.code] = account

    def find(self, code):
        """The registered account, or None: accounts need not be registered to book."""
        return self._accounts.get(code)

    def all(self):
        return [self._accounts[code] for code in sorted(self._accounts)]

    def save(self):
        document = {"accounts": [asdict(account) for account in self.all()]}
        write_atomic(self.path, json.dumps(document, indent=2) + "\n")
