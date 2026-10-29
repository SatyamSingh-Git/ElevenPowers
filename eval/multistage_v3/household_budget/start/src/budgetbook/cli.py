"""The ``budgetbook`` command line.

Every command works on one workspace folder, ``--dir`` (the current folder by
default). Problems the user can fix are printed as ``error: <message>`` with
exit status 1.
"""
import argparse
import json
from pathlib import Path
import sys

from ._generated import CATEGORY_GROUPS, GROUP_TITLES
from .errors import BudgetError, ValidationError
from .importers import all_layouts
from .model.dates import Month, parse_date
from .model.money import format_amount, parse_amount
from .model.records import ACCOUNT_KINDS, FREQUENCIES, Goal, RecurringItem, Rule
from .reports.annual import year_report
from .reports.export import export_month
from .reports.month_end import month_report
from .reports.net_worth import net_worth_report
from .reports.payees import payee_report
from .reports.register import account_register
from .reports.render import RENDERERS, Report, Section, render
from .reports.status import status_report
from .reports.trend import spending_trend
from .rules.engine import RuleBook
from .rules.matchers import MATCHERS, check_pattern
from .services import (accounts, archive, budgets, closing, config, goals, health, importing, ledger, recurring, renames,
                       transfers)
from .services.forecast import forecast
from .services.catalog import Catalog
from .services.reconcile import reconcile
from .services.search import find_transactions
from .storage import files, journal
from .storage.workspace import Workspace


def _print_report(workspace, report, format_name):
    print(render(report, format_name or workspace.settings()["report_format"]), end="")


def _currency(workspace):
    return workspace.settings()["currency"]


def cmd_init(workspace, args):
    workspace.create(args.currency)
    print(f"Created a budget in {workspace.root}")


def cmd_account_add(workspace, args):
    account = accounts.add_account(workspace, args.name, args.kind, args.opening)
    print(f"Added account {account.name} ({account.kind}), opening balance {format_amount(account.opening)}")


def cmd_account_rename(workspace, args):
    renames.rename_account(workspace, args.old, args.new)
    print(f"Renamed account {args.old} to {args.new.strip()}")


def cmd_account_forecast(workspace, args):
    result = forecast(workspace, args.account, args.today, args.days)
    rows = [(line.date.isoformat(), line.description, line.amount, line.balance) for line in result.lines]
    low, on = result.lowest
    _print_report(workspace, Report(f"Forecast {result.account} from {result.start}", [
        Section("Start", ("Date", "Balance"), [(result.start.isoformat(), result.opening)], amounts=("Balance",)),
        Section("Due", ("Date", "Item", "Amount", "Balance"), rows, amounts=("Amount", "Balance")),
        Section("Lowest", ("Date", "Balance"), [(on.isoformat(), low)], amounts=("Balance",)),
    ]), args.format)


def cmd_account_list(workspace, args):
    known = files.load_accounts(workspace)
    balance = accounts.balances(workspace)
    rows = [(account.name, account.kind, balance[account.name]) for account in known.values()]
    _print_report(workspace, Report("Accounts", [Section("Accounts", ("Account", "Kind", "Balance"), rows,
                                                         amounts=("Balance",))]), args.format)


def cmd_add(workspace, args):
    transaction = ledger.add_transaction(workspace, args.date, args.account, args.payee, args.amount,
                                         args.category, args.memo)
    print(f"Added #{transaction.id}: {transaction.date} {transaction.payee} {format_amount(transaction.amount)}")


def cmd_import(workspace, args):
    text = Path(args.file).read_text(encoding="utf-8-sig")
    result = importing.import_statement(workspace, args.account, text, args.layout, args.dry_run)
    verb = "Would import" if args.dry_run else "Imported"
    print(f"{verb} {len(result.added)} transactions into {args.account} ({result.layout} layout); "
          f"{result.duplicates} already there")
    if args.dry_run:
        for transaction in result.added:
            print(f"  {transaction.date} {transaction.payee} {format_amount(transaction.amount)} "
                  f"{transaction.category or '-'}")
    for problem in result.problems:
        print(f"skipped {problem}", file=sys.stderr)


def cmd_categorise(workspace, args):
    print(f"Filed {ledger.categorise_open_months(workspace)} transactions")


def cmd_file(workspace, args):
    transaction = ledger.set_category(workspace, args.id, args.category)
    print(f"#{transaction.id} is now in {transaction.category or 'no category'}")


def cmd_memo(workspace, args):
    transaction = ledger.set_memo(workspace, args.id, args.memo)
    print(f"#{transaction.id} memo: {transaction.memo or '(none)'}")


def cmd_delete(workspace, args):
    transaction = ledger.delete_transaction(workspace, args.id)
    print(f"Deleted #{transaction.id}: {transaction.date} {transaction.payee}")


def cmd_rule_add(workspace, args):
    check_pattern(args.match, args.pattern)
    Catalog.for_workspace(workspace).require(args.category)
    if args.account:
        accounts.require_account(workspace, args.account)
    rules = files.load_rules(workspace)
    rules.append(Rule(args.match, args.pattern, args.category, args.account))
    files.save_rules(workspace, rules)
    print(f"Added rule {len(rules)}: {args.match} {args.pattern!r} -> {args.category}")


def cmd_rule_remove(workspace, args):
    rules = files.load_rules(workspace)
    if not 1 <= args.position <= len(rules):
        raise ValidationError(f"no rule {args.position}; there are {len(rules)}")
    gone = rules.pop(args.position - 1)
    files.save_rules(workspace, rules)
    print(f"Removed rule {args.position}: {gone.match} {gone.pattern!r} -> {gone.category}")


def cmd_rule_move(workspace, args):
    rules = files.load_rules(workspace)
    for position in (args.position, args.to):
        if not 1 <= position <= len(rules):
            raise ValidationError(f"no rule {position}; there are {len(rules)}")
    rules.insert(args.to - 1, rules.pop(args.position - 1))
    files.save_rules(workspace, rules)
    print(f"Moved rule {args.position} to {args.to}")


def cmd_rule_list(workspace, args):
    rows = [(position, rule.match, rule.pattern, rule.category, rule.account or "any")
            for position, rule in enumerate(files.load_rules(workspace), 1)]
    _print_report(workspace, Report("Rules", [Section("Rules", ("#", "Match", "Pattern", "Category", "Account"),
                                                      rows)]), args.format)


def cmd_rule_check(workspace, args):
    found = RuleBook(files.load_rules(workspace)).first_match(args.payee, args.account)
    if found is None:
        print("No rule matches")
        return 1
    position, rule = found
    print(f"Rule {position} matches: {rule.match} {rule.pattern!r} -> {rule.category}")


def cmd_search(workspace, args):
    category = "" if args.uncategorised else args.category
    found = find_transactions(journal.load_transactions(workspace.transactions_path), payee=args.payee,
                              category=category, account=args.account, month=args.month)
    rows = [(t.id, t.date.isoformat(), t.account, t.payee, t.category or "-", t.amount) for t in found]
    _print_report(workspace, Report(f"Search ({len(rows)} found)", [
        Section("Results", ("Id", "Date", "Account", "Payee", "Category", "Amount"), rows, amounts=("Amount",)),
    ]), args.format)


def cmd_register(workspace, args):
    account = accounts.require_account(workspace, args.account)
    report = account_register(account, journal.load_transactions(workspace.transactions_path), args.month)
    _print_report(workspace, report, args.format)


def cmd_reconcile(workspace, args):
    result = reconcile(workspace, args.account, args.date, args.balance)
    if result.agrees:
        print(f"{result.account} agrees with the statement on {result.on}: {format_amount(result.books)}")
        return 0
    print(f"{result.account} on {result.on}: books {format_amount(result.books)}, "
          f"statement {format_amount(result.statement)}, difference {format_amount(result.difference)}")
    for transaction in result.candidates:
        print(f"  check #{transaction.id}: {transaction.date} {transaction.payee} "
              f"{format_amount(transaction.amount)}")
    return 1


def cmd_category_list(workspace, args):
    rows = [(GROUP_TITLES[group], name) for group, names in Catalog.for_workspace(workspace).by_group()
            for name in names]
    _print_report(workspace, Report("Categories", [Section("Categories", ("Group", "Category"), rows)]),
                  args.format)


def cmd_category_rename(workspace, args):
    renames.rename_category(workspace, args.old, args.new)
    print(f"Renamed category {args.old} to {args.new.strip()}")


def cmd_category_add(workspace, args):
    config.add_category(workspace, args.name, args.group)
    print(f"Added category {args.name.strip()} ({GROUP_TITLES[args.group]})")


def cmd_config_show(workspace, args):
    for key, value in sorted(workspace.settings().items()):
        print(f"{key} = {json.dumps(value)}")


def cmd_config_set(workspace, args):
    print(f"{args.key} = {json.dumps(config.set_value(workspace, args.key, args.value))}")


def cmd_transfers(workspace, args):
    pairs = transfers.file_transfers(workspace)
    print(f"Filed {len(pairs)} transfers")
    for pair in pairs:
        print(f"  #{pair.out.id} {pair.out.account} -> #{pair.into.id} {pair.into.account}: "
              f"{format_amount(pair.into.amount)}")


def cmd_check(workspace, args):
    problems = health.find_problems(workspace)
    for problem in problems:
        print(problem)
    if problems:
        return 1
    print("No problems found")


def cmd_goal_add(workspace, args):
    goal = goals.add_goal(workspace, Goal(args.name, args.account, args.target, args.by))
    print(f"Added goal {goal.name}: {format_amount(goal.target)} in {goal.account} by {goal.by}")


def cmd_goal_remove(workspace, args):
    goals.remove_goal(workspace, args.name)
    print(f"Removed goal {args.name}")


def cmd_goal_progress(workspace, args):
    rows = [(p.goal.name, p.goal.by.isoformat(), p.goal.target, p.saved, p.still_needed, p.per_month)
            for p in goals.progress(workspace, args.on)]
    _print_report(workspace, Report(f"Goals on {args.on}", [
        Section("Goals", ("Goal", "By", "Target", "Saved", "Needed", "Per month"), rows,
                amounts=("Target", "Saved", "Needed", "Per month")),
    ]), args.format)


def cmd_recurring_add(workspace, args):
    item = RecurringItem(args.name, args.account, args.payee, args.amount, args.category, args.every,
                         args.day if args.day is not None else args.start.day, args.start, args.end)
    recurring.add_item(workspace, item)
    print(f"Added recurring item {item.name}")


def cmd_recurring_list(workspace, args):
    rows = [(item.name, item.account, item.payee, item.category or "-",
             f"day {item.day} monthly" if item.every == "month" else f"weekly from {item.start}", item.amount)
            for item in files.load_recurring(workspace)]
    _print_report(workspace, Report("Recurring items", [
        Section("Items", ("Name", "Account", "Payee", "Category", "When", "Amount"), rows, amounts=("Amount",)),
    ]), args.format)


def cmd_recurring_remove(workspace, args):
    recurring.remove_item(workspace, args.name)
    print(f"Removed recurring item {args.name}")


def cmd_recurring_upcoming(workspace, args):
    rows = [(day.isoformat(), item.name, item.account, item.amount)
            for day, item in recurring.upcoming(workspace, args.start, args.end)]
    _print_report(workspace, Report(f"Due {args.start} to {args.end}", [
        Section("Due", ("Date", "Item", "Account", "Amount"), rows, amounts=("Amount",)),
    ]), args.format)


def cmd_recurring_post(workspace, args):
    posted = recurring.post_due(workspace, args.through)
    print(f"Posted {len(posted)} recurring transactions")
    for transaction in posted:
        print(f"  #{transaction.id}: {transaction.date} {transaction.payee} {format_amount(transaction.amount)}")


def cmd_budget_set(workspace, args):
    line = budgets.set_budget(workspace, args.category, args.amount, args.rollover)
    rollover = " with rollover" if line.rollover else ""
    print(f"Budget for {line.category}: {format_amount(line.amount)} a month{rollover}")


def cmd_budget_remove(workspace, args):
    budgets.remove_budget(workspace, args.category)
    print(f"Removed the budget for {args.category}")


def cmd_budget_list(workspace, args):
    rows = [(line.category, line.amount, "yes" if line.rollover else "no")
            for line in files.load_budgets(workspace).values()]
    _print_report(workspace, Report("Budgets", [
        Section("Budgets", ("Category", "Monthly", "Rollover"), rows, amounts=("Monthly",)),
    ]), args.format)


def cmd_budget_suggest(workspace, args):
    rows = list(budgets.suggest(workspace, args.month, args.months).items())
    _print_report(workspace, Report(f"Suggested budgets for {args.month}", [
        Section("Suggestions", ("Category", "Monthly"), rows, amounts=("Monthly",)),
    ]), args.format)


def cmd_budget_status(workspace, args):
    lines = budgets.budget_status(workspace, args.month)
    _print_report(workspace, status_report(args.month, lines, _currency(workspace)), args.format)


def cmd_close(workspace, args):
    data = closing.close_month(workspace, args.month)
    print(f"Closed {data['month']}")


def cmd_reopen(workspace, args):
    closing.reopen_month(workspace, args.month)
    print(f"Reopened {args.month}")


def cmd_report_month(workspace, args):
    transactions = journal.load_transactions(workspace.transactions_path)
    report = month_report(args.month, transactions, Catalog.for_workspace(workspace), _currency(workspace))
    _print_report(workspace, report, args.format)


def cmd_report_year(workspace, args):
    _print_report(workspace, year_report(workspace, args.year, _currency(workspace)), args.format)


def cmd_report_net_worth(workspace, args):
    report = net_worth_report(args.year, files.load_accounts(workspace),
                              journal.load_transactions(workspace.transactions_path), _currency(workspace))
    _print_report(workspace, report, args.format)


def cmd_report_payees(workspace, args):
    if args.last < args.first:
        raise ValidationError("the last date is before the first")
    transactions = journal.load_transactions(workspace.transactions_path)
    report = payee_report(args.first, args.last, transactions, Catalog.for_workspace(workspace),
                          _currency(workspace), args.top)
    _print_report(workspace, report, args.format)


def cmd_report_trend(workspace, args):
    if args.months < 1:
        raise ValidationError("--months must be at least 1")
    transactions = journal.load_transactions(workspace.transactions_path)
    report = spending_trend(args.month, args.months, transactions, Catalog.for_workspace(workspace),
                            _currency(workspace))
    _print_report(workspace, report, args.format)


def cmd_archive(workspace, args):
    moved = archive.archive_year(workspace, args.year)
    print(f"Archived {moved} transactions to {archive.archive_path(workspace, args.year)}")


def cmd_export(workspace, args):
    transactions = journal.load_transactions(workspace.transactions_path)
    text = export_month(args.month, transactions, Catalog.for_workspace(workspace))
    Path(args.file).write_text(text, encoding="utf-8", newline="")
    print(f"Wrote {text.count(chr(10)) - 1} transactions to {args.file}")


def _with_format(parser):
    parser.add_argument("--format", choices=sorted(RENDERERS),
                        help="output format (default: report_format in settings.json)")
    return parser


def build_parser():
    parser = argparse.ArgumentParser(prog="budgetbook", description="Household budgeting in plain files.")
    parser.add_argument("--dir", default=".", help="the budget folder (default: the current folder)")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="start a budget in --dir")
    init.add_argument("--currency", default="GBP")
    init.set_defaults(handler=cmd_init)

    account = commands.add_parser("account", help="add or list accounts").add_subparsers(
        dest="action", required=True)
    add_account = account.add_parser("add")
    add_account.add_argument("name")
    add_account.add_argument("--kind", choices=ACCOUNT_KINDS, default="checking")
    add_account.add_argument("--opening", type=parse_amount, default=0)
    add_account.set_defaults(handler=cmd_account_add)
    _with_format(account.add_parser("list")).set_defaults(handler=cmd_account_list)
    rename_account = account.add_parser("rename")
    rename_account.add_argument("old")
    rename_account.add_argument("new")
    rename_account.set_defaults(handler=cmd_account_rename)
    ahead = _with_format(account.add_parser("forecast", help="project the balance from recurring items"))
    ahead.add_argument("account")
    ahead.add_argument("--today", type=parse_date, required=True)
    ahead.add_argument("--days", type=int, default=30)
    ahead.set_defaults(handler=cmd_account_forecast)

    add = commands.add_parser("add", help="record a transaction by hand")
    add.add_argument("date", type=parse_date)
    add.add_argument("account")
    add.add_argument("payee")
    add.add_argument("amount", type=parse_amount, help="negative for money out")
    add.add_argument("--category", default="")
    add.add_argument("--memo", default="")
    add.set_defaults(handler=cmd_add)

    statement = commands.add_parser("import", help="import a bank statement CSV")
    statement.add_argument("account")
    statement.add_argument("file")
    statement.add_argument("--layout", choices=[layout.name for layout in all_layouts()],
                           help="the statement's layout (default: recognised from its header)")
    statement.add_argument("--dry-run", action="store_true", help="show what would be imported, store nothing")
    statement.set_defaults(handler=cmd_import)

    commands.add_parser("categorize", help="file uncategorised transactions by the rules").set_defaults(
        handler=cmd_categorise)

    file_ = commands.add_parser("file", help="set one transaction's category")
    file_.add_argument("id", type=int)
    file_.add_argument("category", help='"" to clear it')
    file_.set_defaults(handler=cmd_file)

    memo = commands.add_parser("memo", help="set one transaction's memo")
    memo.add_argument("id", type=int)
    memo.add_argument("memo")
    memo.set_defaults(handler=cmd_memo)

    delete = commands.add_parser("delete", help="delete one transaction")
    delete.add_argument("id", type=int)
    delete.set_defaults(handler=cmd_delete)

    rule = commands.add_parser("rule", help="categorisation rules").add_subparsers(dest="action", required=True)
    add_rule = rule.add_parser("add")
    add_rule.add_argument("match", choices=sorted(MATCHERS))
    add_rule.add_argument("pattern")
    add_rule.add_argument("category")
    add_rule.add_argument("--account", default="")
    add_rule.set_defaults(handler=cmd_rule_add)
    _with_format(rule.add_parser("list")).set_defaults(handler=cmd_rule_list)
    remove_rule = rule.add_parser("remove")
    remove_rule.add_argument("position", type=int)
    remove_rule.set_defaults(handler=cmd_rule_remove)
    move_rule = rule.add_parser("move", help="change a rule's place; the first rule that matches wins")
    move_rule.add_argument("position", type=int)
    move_rule.add_argument("to", type=int)
    move_rule.set_defaults(handler=cmd_rule_move)
    check_rule = rule.add_parser("test", help="show which rule would file a payee")
    check_rule.add_argument("payee")
    check_rule.add_argument("--account", default="")
    check_rule.set_defaults(handler=cmd_rule_check)

    search = _with_format(commands.add_parser("search", help="find transactions"))
    search.add_argument("--payee", default="")
    search.add_argument("--category")
    search.add_argument("--uncategorised", action="store_true")
    search.add_argument("--account", default="")
    search.add_argument("--month", type=Month.parse)
    search.set_defaults(handler=cmd_search)

    register = _with_format(commands.add_parser("register", help="an account's transactions and balance"))
    register.add_argument("account")
    register.add_argument("--month", type=Month.parse)
    register.set_defaults(handler=cmd_register)

    check = commands.add_parser("reconcile", help="compare an account with a statement balance")
    check.add_argument("account")
    check.add_argument("date", type=parse_date)
    check.add_argument("balance", type=parse_amount)
    check.set_defaults(handler=cmd_reconcile)

    category = commands.add_parser("category", help="list or add categories").add_subparsers(
        dest="action", required=True)
    _with_format(category.add_parser("list")).set_defaults(handler=cmd_category_list)
    add_category = category.add_parser("add")
    add_category.add_argument("name")
    add_category.add_argument("group", choices=CATEGORY_GROUPS)
    add_category.set_defaults(handler=cmd_category_add)
    rename_category = category.add_parser("rename")
    rename_category.add_argument("old")
    rename_category.add_argument("new")
    rename_category.set_defaults(handler=cmd_category_rename)

    settings = commands.add_parser("config", help="show or change settings").add_subparsers(
        dest="action", required=True)
    settings.add_parser("show").set_defaults(handler=cmd_config_show)
    set_value = settings.add_parser("set")
    set_value.add_argument("key")
    set_value.add_argument("value")
    set_value.set_defaults(handler=cmd_config_set)

    commands.add_parser("transfers", help="file transfers between your own accounts").set_defaults(
        handler=cmd_transfers)
    commands.add_parser("check", help="look for inconsistencies between the files").set_defaults(
        handler=cmd_check)

    goal = commands.add_parser("goal", help="savings goals").add_subparsers(dest="action", required=True)
    add_goal = goal.add_parser("add")
    add_goal.add_argument("name")
    add_goal.add_argument("account")
    add_goal.add_argument("target", type=parse_amount)
    add_goal.add_argument("--by", type=parse_date, required=True)
    add_goal.set_defaults(handler=cmd_goal_add)
    remove_goal = goal.add_parser("remove")
    remove_goal.add_argument("name")
    remove_goal.set_defaults(handler=cmd_goal_remove)
    goal_progress = _with_format(goal.add_parser("progress"))
    goal_progress.add_argument("--on", type=parse_date, required=True, help="the date to measure on")
    goal_progress.set_defaults(handler=cmd_goal_progress)

    put_away = commands.add_parser("archive", help="move a closed year out of the transactions file")
    put_away.add_argument("year", type=int)
    put_away.set_defaults(handler=cmd_archive)

    export = commands.add_parser("export", help="write a month's transactions as CSV")
    export.add_argument("month", type=Month.parse)
    export.add_argument("file")
    export.set_defaults(handler=cmd_export)

    repeat = commands.add_parser("recurring", help="recurring items").add_subparsers(
        dest="action", required=True)
    add_item = repeat.add_parser("add")
    add_item.add_argument("name")
    add_item.add_argument("account")
    add_item.add_argument("payee")
    add_item.add_argument("amount", type=parse_amount)
    add_item.add_argument("--category", default="")
    add_item.add_argument("--every", choices=FREQUENCIES, default="month")
    add_item.add_argument("--day", type=int, help="day of the month (default: the start date's day)")
    add_item.add_argument("--start", type=parse_date, required=True)
    add_item.add_argument("--end", type=parse_date)
    add_item.set_defaults(handler=cmd_recurring_add)
    _with_format(repeat.add_parser("list")).set_defaults(handler=cmd_recurring_list)
    remove_item = repeat.add_parser("remove")
    remove_item.add_argument("name")
    remove_item.set_defaults(handler=cmd_recurring_remove)
    due = _with_format(repeat.add_parser("upcoming"))
    due.add_argument("start", type=parse_date)
    due.add_argument("end", type=parse_date)
    due.set_defaults(handler=cmd_recurring_upcoming)
    post = repeat.add_parser("post", help="post everything due")
    post.add_argument("--through", type=parse_date, required=True)
    post.set_defaults(handler=cmd_recurring_post)

    budget = commands.add_parser("budget", help="monthly budgets").add_subparsers(dest="action", required=True)
    set_budget = budget.add_parser("set")
    set_budget.add_argument("category")
    set_budget.add_argument("amount", type=parse_amount)
    set_budget.add_argument("--rollover", action="store_true", help="carry what is left into the next month")
    set_budget.set_defaults(handler=cmd_budget_set)
    remove_budget = budget.add_parser("remove")
    remove_budget.add_argument("category")
    remove_budget.set_defaults(handler=cmd_budget_remove)
    _with_format(budget.add_parser("list")).set_defaults(handler=cmd_budget_list)
    suggestion = _with_format(budget.add_parser("suggest", help="budgets from recent spending"))
    suggestion.add_argument("month", type=Month.parse)
    suggestion.add_argument("--months", type=int, default=3, choices=range(1, 13), metavar="1-12")
    suggestion.set_defaults(handler=cmd_budget_suggest)
    status = _with_format(budget.add_parser("status"))
    status.add_argument("month", type=Month.parse)
    status.set_defaults(handler=cmd_budget_status)

    close = commands.add_parser("close", help="close a month and write its month file")
    close.add_argument("month", type=Month.parse)
    close.set_defaults(handler=cmd_close)

    reopen = commands.add_parser("reopen", help="reopen a closed month")
    reopen.add_argument("month", type=Month.parse)
    reopen.set_defaults(handler=cmd_reopen)

    report = commands.add_parser("report", help="month-end and yearly reports").add_subparsers(
        dest="action", required=True)
    month = _with_format(report.add_parser("month"))
    month.add_argument("month", type=Month.parse)
    month.set_defaults(handler=cmd_report_month)
    year = _with_format(report.add_parser("year"))
    year.add_argument("year", type=int)
    year.set_defaults(handler=cmd_report_year)
    worth = _with_format(report.add_parser("net-worth"))
    worth.add_argument("year", type=int)
    worth.set_defaults(handler=cmd_report_net_worth)
    spenders = _with_format(report.add_parser("payees"))
    spenders.add_argument("first", type=parse_date)
    spenders.add_argument("last", type=parse_date)
    spenders.add_argument("--top", type=int)
    spenders.set_defaults(handler=cmd_report_payees)
    trend = _with_format(report.add_parser("trend"))
    trend.add_argument("month", type=Month.parse, help="the last month shown")
    trend.add_argument("--months", type=int, default=6)
    trend.set_defaults(handler=cmd_report_trend)
    return parser


def main(argv=None):
    try:
        # Argument types raise BudgetError, which argparse lets through to be reported here.
        args = build_parser().parse_args(argv)
        workspace = Workspace(args.dir)
        if args.command != "init":
            workspace.require()
        return args.handler(workspace, args) or 0
    except BudgetError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
