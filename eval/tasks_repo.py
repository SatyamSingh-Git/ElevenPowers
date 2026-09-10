"""Tasks where the bug is not where the symptom is.

Two suites of single-function bugs both scored about 88 percent for a plain
agent, and the second was built with careful traps. Trickier edge cases are not
the difficulty lever: a self-contained function with a stated contract is inside
the model's competence whatever the edge case is.

These are built the other way. The symptom appears in one file and the cause
lives in another, or the obvious fix repairs the reported case and breaks a
second consumer the visible suite does not cover. Both are the ordinary shape of
a bug in a real repository, and both are what verification is supposed to catch.

The rule that decides whether a task is worth anything, learned over four
calibration rounds and then found to be the field's:

    a task measures verification only if running the existing suite would catch
    the fix an agent reaches for first.

Where it would not, no amount of evidence-gathering helps and the task measures
raw capability instead. Every task here whose naive fix left the visible suite
green was failed identically by a weak and a strong model; every task whose
naive fix turned it red was failed by the weak model and resolved by the strong
one.

This is SWE-bench's structure under other names: their FAIL_TO_PASS is the
hidden test, their PASS_TO_PASS is the visible suite a naive fix must break.
Each task therefore records the naive fix as data, so the property is a test
rather than a good intention.
"""

from __future__ import annotations

from .task import Task

REPO: list[Task] = [
    Task(
        name="totals_short",
        prompt=(
            "Our monthly ledger totals come out a few cents short, and the gap gets "
            "bigger the more rows there are. Please fix it."
        ),
        files={
            "src/parse.py": '''"""Reading one row of the ledger file."""


def parse_row(line):
    """A row as (description, amount in whole cents)."""
    description, amount = line.rsplit(",", 1)
    return description.strip(), int(float(amount) * 100)
''',
            "src/report.py": '''"""Summing a ledger into a report."""

from src.parse import parse_row


def total_cents(lines):
    """The total of every row, in cents."""
    return sum(amount for _, amount in (parse_row(line) for line in lines))


def render(lines):
    return f"total ${total_cents(lines) / 100:.2f}"
''',
            "tests/test_report.py": '''from src.report import render, total_cents


def test_simple_total():
    assert total_cents(["rent,100.00", "power,25.50"]) == 12550


def test_render():
    assert render(["rent,100.00"]) == "total $100.00"
''',
        },
        hidden='''from src.parse import parse_row
from src.report import total_cents


def test_awkward_amounts_are_exact():
    assert parse_row("coffee,0.29")[1] == 29
    assert parse_row("bus,0.57")[1] == 57
    assert parse_row("lunch,1.15")[1] == 115


def test_many_rows_do_not_drift():
    lines = ["item,0.29"] * 100
    assert total_cents(lines) == 2900
''',
        why="the symptom is in the report and the cause is float truncation in the parser",
    ),
    Task(
        name="credit_sign",
        naive=('src/money.py', '"""Formatting amounts for display."""\n\n\ndef format_money(cents):\n    """`cents` as a currency string."""\n    return f"${cents / 100:.2f}"\n'),
        prompt=(
            "Credit notes on an invoice are printed as though they were charges, so "
            "an invoice with a credit reads as costing more than it does. "
            "Please fix it."
        ),
        files={
            "src/money.py": '''"""Formatting amounts for display."""


def format_money(cents):
    """`cents` as a currency string."""
    return f"${abs(cents) / 100:.2f}"
''',
            "src/invoice.py": '''"""Invoice lines. Credits are negative amounts."""

from src.money import format_money


def line(description, cents):
    return f"{description}: {format_money(cents)}"
''',
            "src/receipt.py": '''"""Receipt lines. A refund is a negative amount, shown as a positive
figure with the word refunded after it."""

from src.money import format_money


def line(description, cents):
    if cents < 0:
        return f"{description}: {format_money(cents)} refunded"
    return f"{description}: {format_money(cents)}"
''',
            "tests/test_documents.py": '''from src.invoice import line as invoice_line
from src.receipt import line as receipt_line


def test_invoice_charge():
    assert invoice_line("hosting", 1500) == "hosting: $15.00"


def test_receipt_refund():
    assert receipt_line("hosting", -1500) == "hosting: $15.00 refunded"
''',
        },
        hidden='''from src.invoice import line as invoice_line
from src.receipt import line as receipt_line


def test_invoice_credit_reads_as_a_credit():
    assert invoice_line("goodwill", -500) == "goodwill: -$5.00"


def test_receipt_refund_is_unchanged():
    assert receipt_line("hosting", -1500) == "hosting: $15.00 refunded"


def test_charges_are_unchanged_on_both():
    assert invoice_line("hosting", 1500) == "hosting: $15.00"
    assert receipt_line("hosting", 1500) == "hosting: $15.00"
''',
        why="removing the abs fixes the invoice and breaks the receipt, which the visible suite covers only for the passing case",
    ),
    Task(
        name="stale_admin",
        naive=('src/store.py', '"""User lookups."""\n\n\ndef get_user(db, uid):\n    return db.fetch(uid)\n\n\ndef save_user(db, uid, record):\n    db.write(uid, record)\n\n\ndef reset():\n    pass\n'),
        prompt=(
            "Edits made in the admin page do not show up on the site until the "
            "process is restarted. Please fix it."
        ),
        files={
            "src/store.py": '''"""User lookups, cached because the database call is slow."""

_cache = {}


def get_user(db, uid):
    """The user record for `uid`."""
    if uid not in _cache:
        _cache[uid] = db.fetch(uid)
    return _cache[uid]


def save_user(db, uid, record):
    """Store a changed user record."""
    db.write(uid, record)


def reset():
    _cache.clear()
''',
            "tests/test_store.py": '''from src.store import get_user, reset, save_user


class FakeDB:
    def __init__(self):
        self.rows = {"u1": {"name": "ada"}}
        self.fetches = 0

    def fetch(self, uid):
        self.fetches += 1
        return dict(self.rows[uid])

    def write(self, uid, record):
        self.rows[uid] = dict(record)


def test_reads_a_user():
    reset()
    db = FakeDB()
    assert get_user(db, "u1")["name"] == "ada"


def test_writes_a_user():
    reset()
    db = FakeDB()
    save_user(db, "u1", {"name": "grace"})
    assert db.rows["u1"]["name"] == "grace"


def test_repeated_reads_hit_the_database_once():
    reset()
    db = FakeDB()
    get_user(db, "u1")
    get_user(db, "u1")
    assert db.fetches == 1
''',
        },
        hidden='''from src.store import get_user, reset, save_user
from tests.test_store import FakeDB


def test_a_save_is_visible_to_the_next_read():
    reset()
    db = FakeDB()
    get_user(db, "u1")
    save_user(db, "u1", {"name": "grace"})
    assert get_user(db, "u1")["name"] == "grace"


def test_repeated_reads_still_avoid_the_database():
    reset()
    db = FakeDB()
    get_user(db, "u1")
    get_user(db, "u1")
    get_user(db, "u1")
    assert db.fetches == 1
''',
        why="deleting the cache fixes the symptom and throws away the reason the cache exists",
    ),
    Task(
        name="dropped_rows",
        naive=('src/chunk.py', '"""Splitting a sequence into consecutive batches."""\n\n\ndef batches(items, size):\n    return [items[i:i + size] for i in range(0, len(items), size)]\n'),
        prompt=(
            "Every CSV export is missing its last few rows, unless the number of "
            "rows happens to divide evenly by the batch size. Please fix it."
        ),
        files={
            "src/chunk.py": '''"""Splitting a sequence into consecutive batches."""


def batches(items, size):
    """`items` in consecutive batches of at most `size`, covering all of them."""
    return [items[i:i + size] for i in range(0, len(items) - size + 1, size)]
''',
            "src/pager.py": '''"""Page counting for the results footer."""

from src.chunk import batches


def page_count(items, size):
    """How many full pages of `size` items there are."""
    return len(batches(items, size))
''',
            "src/export.py": '''"""Writing rows out in batches."""

from src.chunk import batches


def export(rows, size=5):
    """Every row, in order."""
    written = []
    for batch in batches(rows, size):
        written.extend(batch)
    return written
''',
            "tests/test_export.py": '''from src.chunk import batches
from src.export import export
from src.pager import page_count


def test_exports_an_exact_multiple():
    assert export(list(range(10)), size=5) == list(range(10))


def test_batches_an_exact_multiple():
    assert batches([1, 2, 3, 4, 5, 6], 3) == [[1, 2, 3], [4, 5, 6]]


def test_page_count():
    assert page_count(list(range(10)), 5) == 2


def test_page_count_ignores_a_partial_page():
    assert page_count(list(range(7)), 5) == 1
''',
        },
        hidden='''from src.chunk import batches
from src.export import export
from src.pager import page_count


def test_every_row_is_exported():
    assert export(list(range(7)), size=5) == list(range(7))


def test_the_final_short_batch_is_kept():
    assert batches([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


def test_fewer_items_than_one_batch():
    assert batches([1, 2], 5) == [[1, 2]]


def test_the_footer_still_counts_only_full_pages():
    assert page_count(list(range(7)), 5) == 1
    assert page_count(list(range(10)), 5) == 2
''',
        why="fixing the shared helper makes the page counter, which wanted full pages only, start counting the short one",
    ),
    Task(
        name="percent_display",
        naive=('src/percent.py', '"""Formatting a ratio for display."""\n\n\ndef format_ratio(ratio):\n    return f"{ratio * 100:.0f}%"\n'),
        prompt=(
            "The dashboard is showing conversion rates as 0.12 instead of 12%. "
            "Please fix it."
        ),
        files={
            "src/percent.py": '''"""Formatting a ratio for display.

Returns the ratio itself, to two decimal places, as a string.
\"\"\"


def format_ratio(ratio):
    """`ratio` as a string, to two decimal places."""
    return f"{ratio:.2f}"
''',
            "src/dashboard.py": '''"""The dashboard shows rates as a percentage."""

from src.percent import format_ratio


def conversion(rate):
    return f"conversion {format_ratio(rate)}"
''',
            "src/export.py": '''"""The CSV export carries the raw ratio, which downstream tools parse."""

from src.percent import format_ratio


def row(name, rate):
    return f"{name},{format_ratio(rate)}"
''',
            "tests/test_display.py": '''from src.dashboard import conversion
from src.export import row


def test_export_row():
    assert row("signups", 0.12) == "signups,0.12"


def test_dashboard_renders_something():
    assert conversion(0.12).startswith("conversion ")
''',
        },
        hidden='''from src.dashboard import conversion
from src.export import row
from src.percent import format_ratio


def test_the_dashboard_shows_a_percentage():
    assert conversion(0.12) == "conversion 12%"
    assert conversion(0.5) == "conversion 50%"


def test_the_export_still_carries_the_raw_ratio():
    assert row("signups", 0.12) == "signups,0.12"
    assert row("signups", 0.5) == "signups,0.50"


def test_the_shared_helper_is_unchanged():
    assert format_ratio(0.12) == "0.12"
''',
        why="the tempting fix is to make the shared formatter multiply by 100, which corrupts the export",
    ),
    Task(
        name="search_misses",
        prompt=(
            "Searching the staff directory for a name with a space in it returns "
            "nothing, even though the person is listed. Please fix it."
        ),
        files={
            "src/normalise.py": '''"""The lookup key for a name: case and spacing are ignored."""


def key(text):
    """The form a name is indexed under."""
    return text.lower().replace(" ", "")
''',
            "src/index.py": '''"""Building the directory index."""

from src.normalise import key


def build(names):
    """An index from lookup key to the name as written."""
    return {key(name): name for name in names}
''',
            "src/search.py": '''"""Looking a name up in the directory."""


def find(index, query):
    """The name matching `query`, or None."""
    return index.get(query.lower())
''',
            "tests/test_search.py": '''from src.index import build
from src.search import find

INDEX = build(["Ada", "Grace"])


def test_finds_a_name():
    assert find(INDEX, "ada") == "Ada"


def test_is_case_insensitive():
    assert find(INDEX, "GRACE") == "Grace"
''',
        },
        hidden='''from src.index import build
from src.normalise import key
from src.search import find

INDEX = build(["Ada Lovelace", "Grace Hopper"])


def test_finds_a_name_with_a_space():
    assert find(INDEX, "Ada Lovelace") == "Ada Lovelace"


def test_still_case_insensitive():
    assert find(INDEX, "grace hopper") == "Grace Hopper"


def test_a_query_without_the_space_still_finds_it():
    assert find(INDEX, "adalovelace") == "Ada Lovelace"


def test_the_index_form_is_unchanged():
    assert key("Ada Lovelace") == "adalovelace"
''',
        why="the tempting fix is to stop ignoring spacing in the index, which breaks lookups that omit it",
    ),
]


# Calibrated at 100 percent for a plain agent: single-function bugs by shape,
# kept for coverage but not part of the measuring instrument.
EASY: list[Task] = [
    Task(
        name="duplicate_signups",
        prompt=(
            "Some people are ending up with two accounts on the same email address. "
            "Please fix it."
        ),
        files={
            "src/signup.py": '''"""Registering an account.

Addresses are stored normalised: trimmed and lowercased.
"""

import re

VALID = re.compile(r"^\\s*[^@\\s]+@[^@\\s]+\\.[^@\\s]+\\s*$")


class Duplicate(Exception):
    pass


def register(users, email):
    """Add `email` to `users`, or raise Duplicate."""
    if not VALID.match(email):
        raise ValueError(email)
    if email in users:
        raise Duplicate(email)
    users.add(email.strip().lower())
    return email.strip().lower()
''',
            "tests/test_signup.py": '''import pytest

from src.signup import Duplicate, register


def test_registers():
    users = set()
    assert register(users, "ada@example.com") == "ada@example.com"


def test_rejects_an_exact_repeat():
    users = set()
    register(users, "ada@example.com")
    with pytest.raises(Duplicate):
        register(users, "ada@example.com")
''',
        },
        hidden='''import pytest

from src.signup import Duplicate, register


def test_case_does_not_create_a_second_account():
    users = set()
    register(users, "ada@example.com")
    with pytest.raises(Duplicate):
        register(users, "Ada@Example.com")


def test_surrounding_space_does_not_either():
    users = set()
    register(users, "ada@example.com")
    with pytest.raises(Duplicate):
        register(users, "  ada@example.com  ")


def test_what_is_stored_is_still_normalised():
    users = set()
    register(users, "  Ada@Example.com ")
    assert users == {"ada@example.com"}
''',
        why="the duplicate check runs on the raw address while the stored form is normalised",
    ),
    Task(
        name="env_ignored",
        prompt=(
            "On staging, setting DATABASE_URL in the environment does not override "
            "what is in the config file, so deploys keep pointing at the wrong "
            "database. Please fix it."
        ),
        files={
            "src/settings.py": '''"""Resolving one setting.

Precedence, highest first: the environment, then the config file, then the
built-in default.
"""


def resolve(key, env, file, defaults):
    """The value of `key`."""
    if key in file:
        return file[key]
    if key in env:
        return env[key]
    return defaults.get(key)
''',
            "tests/test_settings.py": '''from src.settings import resolve

DEFAULTS = {"PORT": "8000", "DATABASE_URL": "sqlite://local", "LOG_LEVEL": "info"}


def test_file_beats_the_default():
    assert resolve("PORT", {}, {"PORT": "9000"}, DEFAULTS) == "9000"


def test_default_when_nothing_is_set():
    assert resolve("LOG_LEVEL", {}, {}, DEFAULTS) == "info"
''',
        },
        hidden='''from src.settings import resolve

DEFAULTS = {"PORT": "8000", "DATABASE_URL": "sqlite://local", "LOG_LEVEL": "info"}


def test_environment_beats_the_file_for_every_key():
    for key in ("DATABASE_URL", "PORT", "LOG_LEVEL"):
        assert resolve(key, {key: "from-env"}, {key: "from-file"}, DEFAULTS) == "from-env"


def test_file_still_beats_the_default():
    assert resolve("PORT", {}, {"PORT": "9000"}, DEFAULTS) == "9000"


def test_default_still_applies():
    assert resolve("LOG_LEVEL", {}, {}, DEFAULTS) == "info"
''',
        why="the reported key is one of several; special-casing it leaves the others wrong",
    ),
    Task(
        name="bad_key_retried",
        prompt=(
            "When our API key is wrong, the failure takes three times as long to "
            "surface as it should and the message we end up showing is unhelpful. "
            "Please fix it."
        ),
        files={
            "src/client.py": '''"""Calling an upstream service, retrying transient failures.

A permanent failure such as a rejected credential should surface at once; only
transient failures are worth another attempt.
"""


class AuthError(Exception):
    pass


class Transient(Exception):
    pass


def call(fn, attempts=3):
    """Call `fn`, retrying while it fails transiently."""
    last = None
    for _ in range(attempts):
        try:
            return fn()
        except Exception as exc:
            last = exc
    raise last
''',
            "tests/test_client.py": '''import pytest

from src.client import Transient, call


def test_succeeds_first_time():
    assert call(lambda: "ok") == "ok"


def test_retries_a_transient_failure():
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise Transient("later")
        return "ok"

    assert call(flaky) == "ok"
''',
        },
        hidden='''import pytest

from src.client import AuthError, Transient, call


def test_a_rejected_credential_is_not_retried():
    calls = []

    def bad_key():
        calls.append(1)
        raise AuthError("nope")

    with pytest.raises(AuthError):
        call(bad_key)
    assert len(calls) == 1


def test_transient_failures_are_still_retried():
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise Transient("later")
        return "ok"

    assert call(flaky) == "ok"
    assert len(calls) == 3
''',
        why="catching everything means a permanent failure spends every attempt before surfacing",
    ),
]
