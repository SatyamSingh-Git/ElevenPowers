"""The small JSON files of a workspace: accounts, rules, budgets, recurring items and goals.

Amounts in these files are decimal text such as ``"-950.00"`` so that people
can edit them by hand.
"""
from ..errors import BudgetError
from ..model.dates import parse_date
from ..model.money import decimal_text, parse_amount
from ..model.records import Account, BudgetLine, Goal, RecurringItem, Rule
from .workspace import read_json, write_json


def _fields(entry, path, *names):
    missing = [name for name in names if name not in entry]
    if missing:
        raise BudgetError(f"{path.name}: an entry is missing {missing[0]}")
    return [entry[name] for name in names]


def load_accounts(workspace):
    path = workspace.accounts_path
    accounts = {}
    for entry in read_json(path, []):
        name, kind, opening = _fields(entry, path, "name", "kind", "opening")
        accounts[name] = Account(name, kind, parse_amount(opening))
    return accounts


def save_accounts(workspace, accounts):
    write_json(workspace.accounts_path, [
        {"name": account.name, "kind": account.kind, "opening": decimal_text(account.opening)}
        for account in accounts.values()
    ])


def load_rules(workspace):
    path = workspace.rules_path
    rules = []
    for entry in read_json(path, []):
        match, pattern, category = _fields(entry, path, "match", "pattern", "category")
        rules.append(Rule(match, pattern, category, entry.get("account", "")))
    return rules


def save_rules(workspace, rules):
    entries = []
    for rule in rules:
        entry = {"match": rule.match, "pattern": rule.pattern, "category": rule.category}
        if rule.account:
            entry["account"] = rule.account
        entries.append(entry)
    write_json(workspace.rules_path, entries)


def load_budgets(workspace):
    path = workspace.budgets_path
    budgets = {}
    for category, entry in sorted(read_json(path, {}).items()):
        (amount,) = _fields(entry, path, "amount")
        budgets[category] = BudgetLine(category, parse_amount(amount), bool(entry.get("rollover", False)))
    return budgets


def save_budgets(workspace, budgets):
    write_json(workspace.budgets_path, {
        line.category: {"amount": decimal_text(line.amount), "rollover": line.rollover}
        for line in sorted(budgets.values(), key=lambda line: line.category)
    })


def load_recurring(workspace):
    path = workspace.recurring_path
    items = []
    for entry in read_json(path, []):
        name, account, payee, amount, category, every, day, start = _fields(
            entry, path, "name", "account", "payee", "amount", "category", "every", "day", "start")
        end = entry.get("end")
        items.append(RecurringItem(name, account, payee, parse_amount(amount), category, every, int(day),
                                   parse_date(start), parse_date(end) if end else None))
    return items


def save_recurring(workspace, items):
    entries = []
    for item in items:
        entry = {
            "name": item.name,
            "account": item.account,
            "payee": item.payee,
            "amount": decimal_text(item.amount),
            "category": item.category,
            "every": item.every,
            "day": item.day,
            "start": item.start.isoformat(),
        }
        if item.end:
            entry["end"] = item.end.isoformat()
        entries.append(entry)
    write_json(workspace.recurring_path, entries)


def load_goals(workspace):
    path = workspace.goals_path
    goals = []
    for entry in read_json(path, []):
        name, account, target, by = _fields(entry, path, "name", "account", "target", "by")
        goals.append(Goal(name, account, parse_amount(target), parse_date(by)))
    return goals


def save_goals(workspace, goals):
    write_json(workspace.goals_path, [
        {"name": goal.name, "account": goal.account, "target": decimal_text(goal.target),
         "by": goal.by.isoformat()}
        for goal in goals
    ])
