from datetime import date
from decimal import Decimal
import json

from payroll.model.timesheet import TimesheetEntry


def write_employees(data, *records):
    data.employees.write_text(json.dumps({"employees": list(records)}), encoding="utf-8")


def hourly(employee_id="E001", rate="20.00", **extra):
    return {"id": employee_id, "name": f"Person {employee_id}", "pay_type": "hourly", "rate": rate,
            "bank_account": "12-3456-7890123-00", **extra}


def salaried(employee_id="S001", salary="52000.00", **extra):
    return {"id": employee_id, "name": f"Person {employee_id}", "pay_type": "salaried", "rate": salary,
            "bank_account": "98-7654-3210987-00", **extra}


def entry(employee_id, day, hours, kind="work"):
    return TimesheetEntry(employee_id, date.fromisoformat(day), Decimal(hours), kind)
