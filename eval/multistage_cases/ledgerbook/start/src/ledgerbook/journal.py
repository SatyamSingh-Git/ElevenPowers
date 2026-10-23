"""Writing the journal file.

A journal is UTF-8 text with one JSON object per line: a header first, then
"open" and "txn" records in the order they happened. replay.load_journal reads
it back.
"""
import json
from pathlib import Path

from .errors import LedgerError
from .money import DEFAULT_CURRENCY, currency_digits

FORMAT_VERSION = 1


def _line(record):
    return json.dumps(record, ensure_ascii=False) + "\n"


def header_record(currency):
    return {"ledgerbook": FORMAT_VERSION, "currency": currency}


def open_record(account):
    return {"type": "open", "account": account}


def transaction_record(txn):
    return {
        "type": "txn",
        "date": txn.date,
        "description": txn.description,
        "postings": [{"account": p.account, "amount": p.amount} for p in txn.postings],
    }


class JournalWriter:
    """Appends records to an existing journal file."""

    def __init__(self, path, currency=DEFAULT_CURRENCY):
        self.path = Path(path)
        self.currency = currency

    @classmethod
    def create(cls, path, currency=DEFAULT_CURRENCY):
        """Start a new journal holding only its header; refuses to overwrite."""
        currency_digits(currency)
        path = Path(path)
        try:
            with path.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(_line(header_record(currency)))
        except FileExistsError:
            raise LedgerError(f"journal already exists: {path}") from None
        return cls(path, currency)

    def append_open(self, account):
        self._append(open_record(account))

    def append(self, txn):
        self._append(transaction_record(txn))

    def _append(self, record):
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(_line(record))


def write_journal(path, ledger):
    """Write all of `ledger` to `path`, replacing any file already there."""
    records = [header_record(ledger.currency)]
    records += [open_record(account.name) for account in ledger.chart]
    records += [transaction_record(txn) for txn in ledger.transactions]
    Path(path).write_text("".join(_line(record) for record in records), encoding="utf-8", newline="\n")
