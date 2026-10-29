"""`payroll journal`: the bookkeeping entry for a pay run, ready to post to the ledger."""
import csv
import io

from payroll.model.money import ZERO, format_money, plain_money, total
from payroll.reports.formatting import table

COLUMNS = ("account", "debit", "credit")


def journal_lines(run):
    """(account, debit, credit) lines. The wage expense is the gross pay, which is paid out as
    tax, deductions and net pay, so the debits and credits always balance."""
    return [
        ("Wages expense", run.total("gross"), ZERO),
        ("Tax payable", ZERO, run.total("tax")),
        ("Deductions payable", ZERO, run.total("deductions")),
        ("Net wages payable", ZERO, run.total("net")),
    ]


def render_journal_text(run, lines):
    rows = [[account, _cell(debit), _cell(credit)] for account, debit, credit in lines]
    rows.append(["total", format_money(total(line[1] for line in lines)), format_money(total(line[2] for line in lines))])
    return f"Journal for {run.period.describe()}\n\n" + table(COLUMNS, rows, numeric=(1, 2))


def render_journal_csv(run, lines):
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(COLUMNS)
    for account, debit, credit in lines:
        writer.writerow([account, plain_money(debit), plain_money(credit)])
    return out.getvalue()


def _cell(amount):
    return format_money(amount) if amount else ""


JOURNAL_FORMATS = {
    "text": render_journal_text,
    "csv": render_journal_csv,
}
