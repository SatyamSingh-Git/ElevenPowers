"""Recording transactions by hand and filing them into categories."""
from dataclasses import replace

from ..errors import NotFound, ValidationError
from ..model.dates import Month
from ..model.records import Transaction
from ..rules.engine import RuleBook
from ..storage import files, journal
from .accounts import require_account
from .catalog import Catalog


def add_transaction(workspace, day, account, payee, amount, category="", memo=""):
    require_account(workspace, account)
    if category:
        Catalog.for_workspace(workspace).require(category)
    if not payee.strip():
        raise ValidationError("payee is empty")
    if amount == 0:
        raise ValidationError("amount must not be zero")
    ensure_open(workspace, day)
    transaction = Transaction(0, day, account, payee.strip(), amount, category, memo.strip(), "manual")
    return journal.append_transactions(workspace.transactions_path, [transaction])[0]


def ensure_open(workspace, day):
    month = Month.of(day)
    if workspace.is_closed(month):
        raise ValidationError(f"month is closed: {month}")


def set_category(workspace, transaction_id, category):
    if category:
        Catalog.for_workspace(workspace).require(category)
    transactions = journal.load_transactions(workspace.transactions_path)
    for position, transaction in enumerate(transactions):
        if transaction.id == transaction_id:
            ensure_open(workspace, transaction.date)
            transactions[position] = replace(transaction, category=category)
            journal.save_transactions(workspace.transactions_path, transactions)
            return transactions[position]
    raise NotFound(f"unknown transaction: {transaction_id}")


def set_memo(workspace, transaction_id, memo):
    transactions = journal.load_transactions(workspace.transactions_path)
    for position, transaction in enumerate(transactions):
        if transaction.id == transaction_id:
            ensure_open(workspace, transaction.date)
            transactions[position] = replace(transaction, memo=memo.strip())
            journal.save_transactions(workspace.transactions_path, transactions)
            return transactions[position]
    raise NotFound(f"unknown transaction: {transaction_id}")


def delete_transaction(workspace, transaction_id):
    transactions = journal.load_transactions(workspace.transactions_path)
    keep = [transaction for transaction in transactions if transaction.id != transaction_id]
    if len(keep) == len(transactions):
        raise NotFound(f"unknown transaction: {transaction_id}")
    gone = next(transaction for transaction in transactions if transaction.id == transaction_id)
    ensure_open(workspace, gone.date)
    journal.save_transactions(workspace.transactions_path, keep)
    return gone


def categorise_open_months(workspace):
    """File uncategorised transactions by the rules, leaving closed months alone. Returns how many."""
    book = RuleBook(files.load_rules(workspace))
    transactions = journal.load_transactions(workspace.transactions_path)
    filed = 0
    for position, transaction in enumerate(transactions):
        if not transaction.uncategorised or workspace.is_closed(Month.of(transaction.date)):
            continue
        category = book.category_for(transaction.payee, transaction.account)
        if category:
            transactions[position] = replace(transaction, category=category)
            filed += 1
    if filed:
        journal.save_transactions(workspace.transactions_path, transactions)
    return filed
