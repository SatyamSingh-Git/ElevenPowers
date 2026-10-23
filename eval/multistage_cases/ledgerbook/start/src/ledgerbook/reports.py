"""Reports over a Ledger: trial balance, account statements and a summary."""
from dataclasses import dataclass

from .money import format_amount

TOTAL_LABEL = "Total"
SUMMARY_LABELS = {
    "assets": "Assets",
    "liabilities": "Liabilities",
    "equity": "Equity",
    "income": "Income",
    "expenses": "Expenses",
    "net_income": "Net income",
}


@dataclass(frozen=True)
class TrialBalanceRow:
    account: str
    debit: int
    credit: int


@dataclass(frozen=True)
class TrialBalance:
    rows: tuple
    total_debit: int
    total_credit: int

    @property
    def balanced(self):
        return self.total_debit == self.total_credit


@dataclass(frozen=True)
class StatementLine:
    date: str
    description: str
    amount: int
    balance: int


def trial_balance(ledger):
    """One row per account with a non-zero balance, in its debit or credit column."""
    rows = tuple(
        TrialBalanceRow(name, max(balance, 0), max(-balance, 0))
        for name, balance in ledger.balances().items()
        if balance
    )
    return TrialBalance(rows, sum(row.debit for row in rows), sum(row.credit for row in rows))


def render_trial_balance(ledger):
    report = trial_balance(ledger)

    def cell(minor):
        return format_amount(minor, ledger.currency) if minor else ""

    body = [(row.account, cell(row.debit), cell(row.credit)) for row in report.rows]
    body.append((TOTAL_LABEL, format_amount(report.total_debit, ledger.currency),
                 format_amount(report.total_credit, ledger.currency)))
    return _table(("Account", "Debit", "Credit"), body, "<>>")


def statement(ledger, account):
    """Every posting to `account` with the running balance after it."""
    lines, running = [], 0
    for txn, amount in ledger.postings(account):
        running += amount
        lines.append(StatementLine(txn.date, txn.description, amount, running))
    return lines


def render_statement(ledger, account):
    currency = ledger.currency
    body = [
        (str(line.date), line.description, format_amount(line.amount, currency),
         format_amount(line.balance, currency))
        for line in statement(ledger, account)
    ]
    return f"{account}\n" + _table(("Date", "Description", "Amount", "Balance"), body, "<<>>")


def summary(ledger):
    """Totals per account type, each positive when it carries its normal balance."""
    totals = {
        "assets": ledger.subtotal("Assets"),
        "liabilities": -ledger.subtotal("Liabilities"),
        "equity": -ledger.subtotal("Equity"),
        "income": -ledger.subtotal("Income"),
        "expenses": ledger.subtotal("Expenses"),
    }
    totals["net_income"] = totals["income"] - totals["expenses"]
    return totals


def render_summary(ledger):
    body = [(SUMMARY_LABELS[key], format_amount(value, ledger.currency)) for key, value in summary(ledger).items()]
    return _table(("Type", "Total"), body, "<>")


def _table(headers, rows, align):
    widths = [max(len(row[i]) for row in (headers, *rows)) for i in range(len(headers))]

    def line(cells):
        padded = (cell.ljust(width) if side == "<" else cell.rjust(width)
                  for cell, width, side in zip(cells, widths, align))
        return "  ".join(padded).rstrip()

    rule = ["-" * width for width in widths]
    return "\n".join([line(headers), line(rule), *(line(row) for row in rows)]) + "\n"
