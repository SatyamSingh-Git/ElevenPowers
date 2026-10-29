"""employees.json: everyone on the payroll, with their pay, allowances and deductions."""
import json

from payroll.errors import PayrollError
from payroll.model.employee import Allowance, Deduction, Employee, employee_problems
from payroll.model.money import parse_money, plain_money
from payroll.rules.allowances import check_kind
from payroll.rules.deductions import parse_params
from payroll.storage.files import write_text_atomic

REQUIRED = ("id", "name", "pay_type", "rate", "bank_account")


def load_employees(data):
    """Employees by id, in id order. No file yet means no employees yet."""
    if not data.employees.exists():
        return {}
    try:
        document = json.loads(data.employees.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise PayrollError(f"employees.json is not valid JSON: {error.msg} on line {error.lineno}") from None
    employees = {}
    for number, record in enumerate(document.get("employees", []), start=1):
        employee = _employee(record, number)
        if employee.id in employees:
            raise PayrollError(f"employees.json: employee {employee.id} is listed twice")
        employees[employee.id] = employee
    return dict(sorted(employees.items()))


def save_employees(data, employees):
    records = [_record(employees[employee_id]) for employee_id in sorted(employees)]
    write_text_atomic(data.employees, json.dumps({"employees": records}, indent=2) + "\n")


def _employee(record, number):
    missing = [key for key in REQUIRED if key not in record]
    if missing:
        raise PayrollError(f"employees.json: employee #{number} has no {missing[0]}")
    where = f"employees.json: employee {record['id']}"
    try:
        employee = Employee(
            id=record["id"],
            name=record["name"],
            pay_type=record["pay_type"],
            rate=parse_money(record["rate"], "rate"),
            bank_account=record["bank_account"],
            active=record.get("active", True),
            department=record.get("department") or "General",
            allowances=tuple(_allowance(item) for item in record.get("allowances", [])),
            deductions=tuple(_deduction(item) for item in record.get("deductions", [])),
        )
    except PayrollError as error:
        raise PayrollError(f"{where}: {error}") from None
    problems = employee_problems(employee)
    if problems:
        raise PayrollError(f"employees.json: {problems[0]}")
    return employee


def _allowance(item):
    check_kind(item.get("kind"))
    amount = parse_money(item.get("amount", ""), "allowance amount")
    if amount <= 0:
        raise PayrollError(f"allowance amount must be more than 0: {item.get('amount')}")
    return Allowance(item["kind"], item.get("label") or item["kind"], amount)


def _deduction(item):
    kind = item.get("kind")
    return Deduction(kind, item.get("label") or kind, parse_params(kind, item))


def _record(employee):
    return {
        "id": employee.id,
        "name": employee.name,
        "pay_type": employee.pay_type,
        "rate": plain_money(employee.rate),
        "bank_account": employee.bank_account,
        "active": employee.active,
        "department": employee.department,
        "allowances": [
            {"kind": allowance.kind, "label": allowance.label, "amount": plain_money(allowance.amount)}
            for allowance in employee.allowances
        ],
        "deductions": [
            {"kind": deduction.kind, "label": deduction.label, **{k: str(v) for k, v in deduction.params.items()}}
            for deduction in employee.deductions
        ],
    }
