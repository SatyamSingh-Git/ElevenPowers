"""A month's transactions as a CSV for an accountant or a spreadsheet."""
import csv
import io

from ..model.money import decimal_text

EXPORT_COLUMNS = ("Date", "Account", "Payee", "Category", "Group", "Amount", "Memo")


def export_month(month, transactions, catalog):
    """Every transaction of `month` by date, with its category's group spelled out."""
    rows = sorted((t for t in transactions if t.date in month), key=lambda t: (t.date, t.id))
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(EXPORT_COLUMNS)
    for transaction in rows:
        writer.writerow([transaction.date.isoformat(), transaction.account, transaction.payee,
                         transaction.category, catalog.group_of(transaction.category),
                         decimal_text(transaction.amount), transaction.memo])
    return out.getvalue()
