"""Who the money went to over any stretch of days."""
from .month_end import summarise
from .render import Report, Section


def payee_report(first, last, transactions, catalog, currency, top=None):
    """Spending per payee from `first` to `last`, both included, biggest first."""
    within = [t for t in transactions if first <= t.date <= last]
    payees = summarise(within, catalog).payees
    total = sum(amount for _, amount in payees)
    shown = payees if top is None else payees[:top]
    rows = [(payee, amount, f"{round(amount * 100 / total)}%") for payee, amount in shown]
    return Report(f"Payees {first} to {last} ({currency})", [
        Section("Payees", ("Payee", "Spent", "Share"), rows, amounts=("Spent",)),
    ])
