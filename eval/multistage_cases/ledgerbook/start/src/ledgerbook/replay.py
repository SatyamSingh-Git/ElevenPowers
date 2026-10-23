"""Replaying a journal file into a Ledger.

Every record goes through the same checks as live input, so a hand-edited
journal that would not balance or names an unopened account is refused, with
the line it came from.
"""
import json
from pathlib import Path

from .errors import JournalError, LedgerError
from .ledger import Ledger
from .transactions import make_transaction

SUPPORTED_VERSIONS = (1,)


def read_records(path):
    """Yield (line number, record) for every non-blank line of the journal."""
    with Path(path).open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise JournalError(number, f"not valid JSON ({exc.msg})") from None
            if not isinstance(record, dict):
                raise JournalError(number, "record is not a JSON object")
            yield number, record


def load_journal(path):
    """Rebuild the Ledger a journal describes; JournalError on the first bad line."""
    records = read_records(path)
    first = next(records, None)
    if first is None:
        raise JournalError(1, "missing header")
    number, header = first
    version = header.get("ledgerbook")
    if version not in SUPPORTED_VERSIONS:
        raise JournalError(number, f"unsupported journal version: {version}")
    try:
        ledger = Ledger(_field(header, "currency"))
    except LedgerError as exc:
        raise JournalError(number, str(exc)) from None
    for number, record in records:
        try:
            _apply(ledger, record)
        except LedgerError as exc:
            raise JournalError(number, str(exc)) from None
    return ledger


def _field(record, name):
    try:
        return record[name]
    except KeyError:
        raise LedgerError(f"missing field: {name}") from None


def _apply(ledger, record):
    kind = _field(record, "type")
    if kind == "open":
        ledger.open(_field(record, "account"))
    elif kind == "txn":
        postings = [(_field(p, "account"), _field(p, "amount")) for p in _field(record, "postings")]
        ledger.post(make_transaction(_field(record, "date"), _field(record, "description"), postings))
    else:
        raise LedgerError(f"unknown record type: {kind}")
