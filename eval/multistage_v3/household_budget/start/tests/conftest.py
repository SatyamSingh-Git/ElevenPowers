import datetime as dt

import pytest

from budgetbook.services.accounts import add_account
from budgetbook.storage.workspace import Workspace


@pytest.fixture
def book(tmp_path):
    workspace = Workspace(tmp_path / "book")
    workspace.create("GBP")
    add_account(workspace, "Current", "checking", 100000)
    return workspace


def day(text):
    return dt.date.fromisoformat(text)
