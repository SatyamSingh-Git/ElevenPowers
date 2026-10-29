"""Changing who is on the payroll: hiring, leaving, and their allowances and deductions."""
from dataclasses import replace

from payroll.errors import PayrollError
from payroll.model.employee import Allowance, Deduction, Employee, employee_problems
from payroll.model.money import parse_money
from payroll.rules.allowances import check_kind
from payroll.rules.deductions import parse_params
from payroll.storage.employee_store import load_employees, save_employees


def find_employee(employees, employee_id):
    try:
        return employees[employee_id]
    except KeyError:
        raise PayrollError(f"unknown employee {employee_id}") from None


def add_employee(data, employee_id, name, pay_type, rate, bank_account, department="General"):
    employees = load_employees(data)
    if employee_id in employees:
        raise PayrollError(f"employee {employee_id} already exists")
    employee = Employee(employee_id, name.strip(), pay_type, parse_money(rate, "rate"), bank_account.strip(),
                        department=department.strip() or "General")
    problems = employee_problems(employee)
    if problems:
        raise PayrollError(problems[0])
    employees[employee_id] = employee
    save_employees(data, employees)
    return employee


def set_active(data, employee_id, active):
    employees = load_employees(data)
    employee = find_employee(employees, employee_id)
    employees[employee_id] = replace(employee, active=active)
    save_employees(data, employees)
    return employees[employee_id]


def update_details(data, employee_id, name=None, bank_account=None, department=None):
    employees = load_employees(data)
    employee = find_employee(employees, employee_id)
    given = {"name": name, "bank_account": bank_account, "department": department}
    changes = {field: value.strip() for field, value in given.items() if value is not None}
    if not changes:
        raise PayrollError("give at least one of --name, --bank-account or --department")
    updated = replace(employee, **changes)
    problems = employee_problems(updated)
    if problems:
        raise PayrollError(problems[0])
    employees[employee_id] = updated
    save_employees(data, employees)
    return updated


def set_rate(data, employee_id, rate):
    employees = load_employees(data)
    employee = find_employee(employees, employee_id)
    new_rate = parse_money(rate, "rate")
    if new_rate <= 0:
        raise PayrollError(f"employee {employee_id}: rate must be more than 0")
    employees[employee_id] = replace(employee, rate=new_rate)
    save_employees(data, employees)
    return employees[employee_id]


def add_allowance(data, employee_id, kind, label, amount):
    check_kind(kind)
    value = parse_money(amount, "allowance amount")
    if value <= 0:
        raise PayrollError(f"allowance amount must be more than 0: {amount}")
    employees = load_employees(data)
    employee = find_employee(employees, employee_id)
    allowance = Allowance(kind, label or kind, value)
    employees[employee_id] = replace(employee, allowances=employee.allowances + (allowance,))
    save_employees(data, employees)
    return allowance


def add_deduction(data, employee_id, kind, label, values):
    """`values` holds the text given for each parameter, by name; unused names are ignored."""
    params = parse_params(kind, values)
    employees = load_employees(data)
    employee = find_employee(employees, employee_id)
    deduction = Deduction(kind, label or kind, params)
    employees[employee_id] = replace(employee, deductions=employee.deductions + (deduction,))
    save_employees(data, employees)
    return deduction


def remove_extra(data, employee_id, label):
    """Removes the allowances and deductions with this label; it is an error if there are none."""
    employees = load_employees(data)
    employee = find_employee(employees, employee_id)
    allowances = tuple(item for item in employee.allowances if item.label != label)
    deductions = tuple(item for item in employee.deductions if item.label != label)
    if len(allowances) + len(deductions) == len(employee.allowances) + len(employee.deductions):
        raise PayrollError(f"employee {employee_id} has nothing labelled {label}")
    employees[employee_id] = replace(employee, allowances=allowances, deductions=deductions)
    save_employees(data, employees)
