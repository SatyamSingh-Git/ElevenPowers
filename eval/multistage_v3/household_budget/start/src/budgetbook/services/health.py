"""Checking that a workspace's files still agree with each other.

Files are plain text and people edit them by hand, so an account can be
renamed in one file and not another. Nothing here changes anything.
"""
from collections import Counter

from ..errors import BudgetError
from ..rules.matchers import check_pattern
from ..storage import files, journal
from .catalog import Catalog


def find_problems(workspace):
    """Every inconsistency found, as sentences; an empty list means the books are sound."""
    try:
        catalog = Catalog.for_workspace(workspace)
        accounts = files.load_accounts(workspace)
        transactions = journal.load_transactions(workspace.transactions_path)
        rules = files.load_rules(workspace)
        budgets = files.load_budgets(workspace)
        items = files.load_recurring(workspace)
    except BudgetError as error:
        return [str(error)]

    problems = []
    for number, count in sorted(Counter(t.id for t in transactions).items()):
        if count > 1:
            problems.append(f"transaction id {number} is used {count} times")
    for transaction in transactions:
        if transaction.account not in accounts:
            problems.append(f"transaction #{transaction.id} is in unknown account {transaction.account}")
        if transaction.category and transaction.category not in catalog.groups:
            problems.append(f"transaction #{transaction.id} is in unknown category {transaction.category}")
    for position, rule in enumerate(rules, 1):
        try:
            check_pattern(rule.match, rule.pattern)
        except BudgetError as error:
            problems.append(f"rule {position}: {error}")
        if rule.category not in catalog.groups:
            problems.append(f"rule {position} files into unknown category {rule.category}")
        if rule.account and rule.account not in accounts:
            problems.append(f"rule {position} is limited to unknown account {rule.account}")
    for category in budgets:
        if category not in catalog.groups:
            problems.append(f"budget for unknown category {category}")
    for item in items:
        if item.account not in accounts:
            problems.append(f"recurring item {item.name} posts to unknown account {item.account}")
        if item.category and item.category not in catalog.groups:
            problems.append(f"recurring item {item.name} files into unknown category {item.category}")
    return problems
