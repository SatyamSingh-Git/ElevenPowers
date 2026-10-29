"""`payroll compare`: how one pay run differs from another, employee by employee."""
from decimal import Decimal

from payroll.model.money import ZERO, format_money
from payroll.reports.formatting import table

# A change in net pay bigger than this share of the earlier amount is flagged.
FLAG_SHARE = Decimal("0.20")


def compare_rows(earlier, later):
    """(employee, name, earlier net, later net, change, flag) for everyone in either run."""
    before = {slip.employee_id: slip for slip in earlier.payslips}
    after = {slip.employee_id: slip for slip in later.payslips}
    rows = []
    for employee_id in sorted(set(before) | set(after)):
        old, new = before.get(employee_id), after.get(employee_id)
        name = (new or old).name
        old_net = old.net if old else ZERO
        new_net = new.net if new else ZERO
        rows.append((employee_id, name, old_net, new_net, new_net - old_net, _flag(old, new)))
    return rows


def _flag(old, new):
    if old is None:
        return "new"
    if new is None:
        return "not paid"
    if old.net and abs(new.net - old.net) > abs(old.net) * FLAG_SHARE:
        return "check"
    return ""


def render_compare(earlier, later, rows):
    header = ("employee", "name", earlier.period.id, later.period.id, "change", "")
    body = [
        [employee_id, name, format_money(old), format_money(new), _signed(change), flag]
        for employee_id, name, old, new, change, flag in rows
    ]
    return table(header, body, numeric=(2, 3, 4))


def _signed(amount):
    return ("+" if amount > 0 else "") + format_money(amount)
