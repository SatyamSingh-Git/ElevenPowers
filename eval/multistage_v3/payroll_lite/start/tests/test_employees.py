from decimal import Decimal

import pytest

from helpers import hourly, write_employees
from payroll.errors import ImportRejected, PayrollError
from payroll.services import employees as staff
from payroll.storage.employee_csv import employees_csv, parse_employees
from payroll.storage.employee_store import load_employees


def test_add_and_change_an_employee(data):
    staff.add_employee(data, "E001", "Ana Lima", "hourly", "25", "11-1111-0000001-00")
    staff.add_deduction(data, "E001", "percent", "Pension", {"rate": "5", "amount": None})
    staff.add_allowance(data, "E001", "per_shift", "Meal", "8")
    staff.set_rate(data, "E001", "26.50")
    employee = load_employees(data)["E001"]
    assert employee.rate == Decimal("26.50")
    assert employee.deductions[0].params == {"rate": Decimal("5")}
    assert employee.allowances[0].amount == Decimal("8.00")
    staff.remove_extra(data, "E001", "Meal")
    assert load_employees(data)["E001"].allowances == ()


def test_employee_fields_are_checked(data):
    with pytest.raises(PayrollError, match="bank account must look like"):
        staff.add_employee(data, "E001", "Ana Lima", "hourly", "25", "1234")
    with pytest.raises(PayrollError, match="unknown employee E404"):
        staff.set_active(data, "E404", False)


def test_bad_records_in_the_file_name_the_employee(data):
    write_employees(data, hourly("E001", deductions=[{"kind": "fixed", "label": "Union"}]))
    with pytest.raises(PayrollError, match="employees.json: employee E001: a fixed deduction needs amount"):
        load_employees(data)


def test_csv_round_trip(data):
    write_employees(data, hourly("E001"), hourly("E002"))
    text = employees_csv(load_employees(data)).replace("E001", "E101").replace("E002", "E102")
    added = parse_employees(text, load_employees(data))
    assert sorted(added) == ["E101", "E102"]


def test_csv_import_rejects_duplicates(data):
    write_employees(data, hourly("E001"))
    text = "id,name,pay_type,rate,bank_account\nE001,Ana,hourly,25,11-1111-0000001-00\n"
    with pytest.raises(ImportRejected) as rejected:
        parse_employees(text, load_employees(data))
    assert rejected.value.problems == ["line 2: employee E001 already exists"]
