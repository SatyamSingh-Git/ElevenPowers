"""The payment file uploaded to the bank: headerless CSV, one row per payment."""
import csv
import io

from payroll.errors import PayrollError
from payroll.model.money import plain_money, total
from payroll.storage.files import write_text_atomic

# The bank cuts longer names off and then rejects the file.
NAME_LENGTH = 20


def reference(period):
    return f"PAY {period.id}"


def bank_rows(run, employees):
    rows = []
    for slip in run.payslips:
        if slip.net <= 0:
            continue
        employee = employees.get(slip.employee_id)
        if employee is None:
            raise PayrollError(f"unknown employee {slip.employee_id}")
        rows.append([employee.bank_account, slip.name[:NAME_LENGTH], plain_money(slip.net), reference(run.period)])
    return rows


def check_rows(rows):
    """The bank rejects a whole file that pays one account twice, so that is caught before writing."""
    seen = set()
    for account, name, *_ in rows:
        if account in seen:
            raise PayrollError(f"two payments to account {account}; check the bank details of {name}")
        seen.add(account)


def write_bank_file(path, rows):
    out = io.StringIO()
    csv.writer(out, lineterminator="\n").writerows(rows)
    write_text_atomic(path, out.getvalue())


def paid_total(run):
    return total(slip.net for slip in run.payslips if slip.net > 0)
