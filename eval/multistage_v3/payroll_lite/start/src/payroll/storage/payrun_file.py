"""runs/<period>.json: a pay run as it was paid, read back for payslips and bank files."""
from datetime import date
from decimal import Decimal
import json

from payroll.errors import PayrollError
from payroll.model.money import plain_money
from payroll.model.payslip import TOTALS, Line, PayRun, Payslip
from payroll.model.period import PayPeriod
from payroll.model.timesheet import format_hours
from payroll.storage.files import write_text_atomic

SCHEMA = 1


def write_payrun(path, run):
    document = {
        "schema": SCHEMA,
        "period": run.period.id,
        "start": run.period.start.isoformat(),
        "end": run.period.end.isoformat(),
        "pay_date": run.period.pay_date.isoformat(),
        "payslips": [_slip_record(slip) for slip in run.payslips],
        "totals": {name: plain_money(run.total(name)) for name in TOTALS},
    }
    write_text_atomic(path, json.dumps(document, indent=2) + "\n")


def read_payrun(path):
    if not path.exists():
        raise PayrollError(f"no pay run for {path.stem}")
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema") != SCHEMA:
        raise PayrollError(f"{path.name}: unsupported pay-run schema {document.get('schema')}")
    period = PayPeriod(
        document["period"],
        date.fromisoformat(document["start"]),
        date.fromisoformat(document["end"]),
        date.fromisoformat(document["pay_date"]),
    )
    return PayRun(period, tuple(_slip(record) for record in document["payslips"]))


def _slip_record(slip):
    record = {"employee_id": slip.employee_id, "name": slip.name}
    record.update({name: plain_money(getattr(slip, name)) for name in TOTALS})
    record["lines"] = [_line_record(line) for line in slip.lines]
    return record


def _line_record(line):
    return {
        "kind": line.kind,
        "label": line.label,
        "hours": None if line.hours is None else format_hours(line.hours),
        "rate": None if line.rate is None else plain_money(line.rate),
        "amount": plain_money(line.amount),
    }


def _slip(record):
    lines = tuple(_line(item) for item in record["lines"])
    return Payslip(record["employee_id"], record["name"], lines, *(Decimal(record[name]) for name in TOTALS))


def _line(record):
    return Line(
        record["kind"],
        record["label"],
        Decimal(record["amount"]),
        hours=None if record["hours"] is None else Decimal(record["hours"]),
        rate=None if record["rate"] is None else Decimal(record["rate"]),
    )
