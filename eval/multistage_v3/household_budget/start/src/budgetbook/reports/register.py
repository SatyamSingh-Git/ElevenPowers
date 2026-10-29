"""An account's register: its transactions in date order with a running balance."""
from .render import Report, Section


def account_register(account, transactions, month=None):
    """The register of `account`, limited to `month` when given.

    The balance always starts from the account's opening balance, so a month's
    first line already includes everything before it.
    """
    balance = account.opening
    rows = []
    for transaction in transactions:
        if transaction.account != account.name:
            continue
        balance += transaction.amount
        if month is None or transaction.date in month:
            rows.append((transaction.date.isoformat(), transaction.payee, transaction.category or "-",
                         transaction.amount, balance))
    title = f"Register {account.name}" + (f" {month}" if month else "")
    return Report(title, [
        Section("Transactions", ("Date", "Payee", "Category", "Amount", "Balance"), rows,
                amounts=("Amount", "Balance")),
    ])
