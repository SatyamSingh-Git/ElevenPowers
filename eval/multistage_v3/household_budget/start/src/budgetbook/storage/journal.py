"""The transactions file: one CSV row per transaction, kept sorted by date."""
import csv
from dataclasses import replace

from ..errors import BudgetError
from ..model.dates import parse_date
from ..model.money import decimal_text, parse_amount
from ..model.records import Transaction

COLUMNS = ("id", "date", "account", "payee", "amount", "category", "memo", "source")


def load_transactions(path):
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None:
            return []
        if tuple(header) != COLUMNS:
            raise BudgetError(f"{path.name} has an unexpected header: {','.join(header)}")
        return [_decode(row, reader.line_num) for row in reader if row]


def append_transactions(path, new):
    """Store `new` under fresh ids and return them as stored."""
    existing = load_transactions(path)
    first = max((t.id for t in existing), default=0) + 1
    stored = [replace(transaction, id=first + offset) for offset, transaction in enumerate(new)]
    save_transactions(path, existing + stored)
    return stored


def save_transactions(path, transactions):
    """Rewrite the whole file with `transactions`."""
    ordered = sorted(transactions, key=lambda t: (t.date, t.id))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(_encode(transaction) for transaction in ordered)


def _encode(transaction):
    return [
        str(transaction.id),
        transaction.date.isoformat(),
        transaction.account,
        transaction.payee,
        decimal_text(transaction.amount),
        transaction.category,
        transaction.memo,
        transaction.source,
    ]


def _decode(row, line):
    if len(row) != len(COLUMNS):
        raise BudgetError(f"transactions file line {line} has {len(row)} fields, expected {len(COLUMNS)}")
    number, day, account, payee, amount, category, memo, source = row
    try:
        return Transaction(int(number), parse_date(day), account, payee, parse_amount(amount),
                           category, memo, source)
    except (ValueError, BudgetError) as error:
        raise BudgetError(f"transactions file line {line} cannot be read: {error}") from None
