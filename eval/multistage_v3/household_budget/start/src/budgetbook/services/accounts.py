"""The household's accounts and what is in them."""
from ..errors import NotFound, ValidationError
from ..model.records import ACCOUNT_KINDS, Account
from ..storage import files, journal


def add_account(workspace, name, kind="checking", opening=0):
    name = name.strip()
    if not name:
        raise ValidationError("account name is empty")
    if kind not in ACCOUNT_KINDS:
        raise ValidationError(f"account kind must be one of: {', '.join(ACCOUNT_KINDS)}")
    accounts = files.load_accounts(workspace)
    if name in accounts:
        raise ValidationError(f"account already exists: {name}")
    accounts[name] = Account(name, kind, opening)
    files.save_accounts(workspace, accounts)
    return accounts[name]


def require_account(workspace, name):
    accounts = files.load_accounts(workspace)
    if name not in accounts:
        raise NotFound(f"unknown account: {name}")
    return accounts[name]


def balances(workspace, through=None):
    """Each account with its balance, counting transactions up to `through` when given."""
    totals = {name: account.opening for name, account in files.load_accounts(workspace).items()}
    for transaction in journal.load_transactions(workspace.transactions_path):
        if transaction.account in totals and (through is None or transaction.date <= through):
            totals[transaction.account] += transaction.amount
    return totals
