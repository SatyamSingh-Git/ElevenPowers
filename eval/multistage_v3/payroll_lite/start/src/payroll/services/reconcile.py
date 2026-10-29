"""Checking the bank's statement against the payment file sent for a period."""
from collections import defaultdict
import csv
from dataclasses import dataclass
from decimal import Decimal

from payroll.errors import PayrollError
from payroll.model.money import parse_money

STATEMENT_COLUMNS = ("date", "account", "reference", "amount")


@dataclass(frozen=True)
class Payment:
    account: str
    name: str
    amount: Decimal
    reference: str


def load_payments(path):
    """The payments in a bank file written by `payroll bank-file`."""
    if not path.exists():
        raise PayrollError(f"no bank file at {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            Payment(account, name, Decimal(amount), reference)
            for account, name, amount, reference in csv.reader(handle)
        ]


def load_statement(path):
    """(account, reference, amount) for every line of a statement exported from the bank."""
    try:
        handle = open(path, newline="", encoding="utf-8")
    except FileNotFoundError:
        raise PayrollError(f"no such file: {path}") from None
    with handle:
        reader = csv.DictReader(handle)
        for column in STATEMENT_COLUMNS:
            if column not in (reader.fieldnames or []):
                raise PayrollError(f"statement is missing column {column}")
        return [
            (row["account"].strip(), row["reference"].strip(), parse_money(row["amount"], "statement amount"))
            for row in reader
        ]


def reconcile(payments, statement):
    """(account, name, status) for each payment, then for statement lines carrying one of our
    references that no payment accounts for."""
    received = defaultdict(list)
    for account, reference, amount in statement:
        received[(account, reference)].append(amount)
    ours = {payment.reference for payment in payments}
    results = []
    for payment in payments:
        amounts = received.get((payment.account, payment.reference))
        if not amounts:
            results.append((payment.account, payment.name, "missing"))
            continue
        paid = amounts.pop(0)
        if paid == payment.amount:
            results.append((payment.account, payment.name, "matched"))
        else:
            results.append((payment.account, payment.name, f"wrong amount: paid {paid}, expected {payment.amount}"))
    for (account, reference), amounts in received.items():
        if reference in ours:
            results.extend((account, reference, "unexpected") for _ in amounts)
    return results


def all_matched(results):
    return all(status == "matched" for _, _, status in results)
