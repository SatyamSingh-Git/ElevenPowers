"""Renaming an account or a category in every file that names it.

Month files are left alone: they record a month as it was when it was closed.
A renamed category with rollover therefore carries nothing into the month
after the rename.
"""
from dataclasses import replace

from ..errors import NotFound, ValidationError
from ..storage import files, journal
from .catalog import Catalog


def rename_account(workspace, old, new):
    new = new.strip()
    accounts = files.load_accounts(workspace)
    if old not in accounts:
        raise NotFound(f"unknown account: {old}")
    if not new:
        raise ValidationError("account name is empty")
    if new in accounts:
        raise ValidationError(f"account already exists: {new}")
    accounts = {(new if name == old else name): (replace(account, name=new) if name == old else account)
                for name, account in accounts.items()}
    files.save_accounts(workspace, accounts)
    transactions = journal.load_transactions(workspace.transactions_path)
    journal.save_transactions(workspace.transactions_path, [
        replace(t, account=new) if t.account == old else t for t in transactions])
    files.save_rules(workspace, [replace(r, account=new) if r.account == old else r
                                 for r in files.load_rules(workspace)])
    files.save_recurring(workspace, [replace(i, account=new) if i.account == old else i
                                     for i in files.load_recurring(workspace)])
    files.save_goals(workspace, [replace(g, account=new) if g.account == old else g
                                 for g in files.load_goals(workspace)])


def rename_category(workspace, old, new):
    """Rename one of the household's own categories; the built-in ones keep their names."""
    new = new.strip()
    settings = workspace.settings()
    extra = settings["extra_categories"]
    if old not in extra:
        if old in Catalog.for_workspace(workspace).groups:
            raise ValidationError(f"built-in categories cannot be renamed: {old}")
        raise NotFound(f"unknown category: {old}")
    if not new:
        raise ValidationError("category name is empty")
    if new in Catalog.for_workspace(workspace).groups:
        raise ValidationError(f"category already exists: {new}")
    settings["extra_categories"] = {(new if name == old else name): group for name, group in extra.items()}
    workspace.save_settings(settings)
    transactions = journal.load_transactions(workspace.transactions_path)
    journal.save_transactions(workspace.transactions_path, [
        replace(t, category=new) if t.category == old else t for t in transactions])
    files.save_rules(workspace, [replace(r, category=new) if r.category == old else r
                                 for r in files.load_rules(workspace)])
    files.save_recurring(workspace, [replace(i, category=new) if i.category == old else i
                                     for i in files.load_recurring(workspace)])
    budgets = files.load_budgets(workspace)
    if old in budgets:
        budgets[new] = replace(budgets.pop(old), category=new)
        files.save_budgets(workspace, budgets)
