"""Each account's balance at the end of every month of a year, and their total."""
from ..model.dates import months_of_year
from .render import Report, Section


def net_worth_report(year, accounts, transactions, currency):
    """Money owed on a credit account is already negative in the ledger, so the plain sum is net worth."""
    names = list(accounts)
    rows = []
    for month in months_of_year(year):
        end = month.last_day
        balance = {name: accounts[name].opening for name in names}
        for transaction in transactions:
            if transaction.account in balance and transaction.date <= end:
                balance[transaction.account] += transaction.amount
        values = [balance[name] for name in names]
        rows.append((str(month), *values, sum(values)))
    columns = ("Month", *names, "Net worth")
    return Report(f"Net worth {year} ({currency})", [Section("Month ends", columns, rows, amounts=columns[1:])])
