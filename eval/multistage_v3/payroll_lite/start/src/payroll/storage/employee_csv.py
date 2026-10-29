"""Adding several employees at once from a spreadsheet saved as CSV."""
import csv
import io

from payroll.errors import ImportRejected, PayrollError
from payroll.model.employee import Employee, employee_problems
from payroll.model.money import parse_money, plain_money

COLUMNS = ("id", "name", "pay_type", "rate", "bank_account")


def parse_employees(text, existing):
    """New employees from the file, or ImportRejected naming every bad row by its line."""
    reader = csv.DictReader(io.StringIO(text))
    columns = [name.strip() for name in reader.fieldnames or []]
    for column in COLUMNS:
        if column not in columns:
            raise PayrollError(f"missing column {column}")
    reader.fieldnames = columns
    added, problems = {}, []
    for row in reader:
        values = {column: (row.get(column) or "").strip() for column in columns}
        problem = None
        try:
            employee = _employee(values)
        except PayrollError as error:
            problem = str(error)
        else:
            if employee.id in existing or employee.id in added:
                problem = f"employee {employee.id} already exists"
            else:
                found = employee_problems(employee)
                if found:
                    problem = found[0]
                else:
                    added[employee.id] = employee
        if problem:
            problems.append(f"line {reader.line_num}: {problem}")
    if problems:
        raise ImportRejected(problems)
    return added


def employees_csv(employees):
    """The same layout `parse_employees` reads, so the file can be edited and imported elsewhere."""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow((*COLUMNS, "department"))
    for employee in employees.values():
        writer.writerow([employee.id, employee.name, employee.pay_type, plain_money(employee.rate),
                         employee.bank_account, employee.department])
    return out.getvalue()


def _employee(values):
    return Employee(
        id=values["id"],
        name=values["name"],
        pay_type=values["pay_type"],
        rate=parse_money(values["rate"], "rate"),
        bank_account=values["bank_account"],
        department=values.get("department") or "General",
    )
