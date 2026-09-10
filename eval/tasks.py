"""Small repositories with a seeded defect, for measuring the submit-resolve gap.

Every task has the same shape, and it is the shape the published measurements of
this problem use. A bug is reported the way a colleague would report it, by
symptom rather than by diagnosis. The visible test suite passes both before and
after the fix, so a green run proves nothing and an agent that stops there will
claim completion having changed nothing that matters. A hidden test, written into
the repository only once the agent has finished, decides whether the work was
actually done.

The gap between the first answer and the second is the whole subject of this
project.

The defects here are deliberate, which is the one place in this repository where
that is true. They are fixtures, chosen because they are the kind of thing that
survives a careless fix: boundaries, remainders, ordering, and the difference
between what a function does and what its happy-path test covers.
"""

from __future__ import annotations

from .task import Task


TASKS: list[Task] = [
    Task(
        name="last_page",
        prompt=(
            "Users report that the last page of search results is missing an entry "
            "whenever the total number of results is not an exact multiple of the "
            "page size. Please fix it."
        ),
        files={
            "src/paging.py": '''"""Slicing a result set into pages."""


def page_slice(items, page, per_page):
    """The items on `page`, counting from 1."""
    start = (page - 1) * per_page
    end = start + per_page
    if end > len(items):
        end = len(items) - 1
    return items[start:end]
''',
            "tests/test_paging.py": '''from src.paging import page_slice

ITEMS = list(range(10))


def test_first_page():
    assert page_slice(ITEMS, 1, 5) == [0, 1, 2, 3, 4]


def test_second_page():
    assert page_slice(ITEMS, 2, 5) == [5, 6, 7, 8, 9]
''',
        },
        hidden='''from src.paging import page_slice


def test_partial_last_page_keeps_every_item():
    assert page_slice(list(range(7)), 2, 5) == [5, 6]


def test_single_item_last_page():
    assert page_slice(list(range(6)), 2, 5) == [5]
''',
        why="the clamp drops the final item, and only on a partial last page",
    ),
    Task(
        name="split_bill",
        prompt=(
            "Our billing reconciliation is off by a few cents. When a charge is "
            "divided between people, the individual shares do not add back up to "
            "the original amount. Please fix it."
        ),
        files={
            "src/money.py": '''"""Dividing an amount in cents between people."""


def split_bill(total_cents, people):
    """Each person's share, in cents."""
    share = total_cents // people
    return [share] * people
''',
            "tests/test_money.py": '''from src.money import split_bill


def test_even_split():
    assert split_bill(100, 4) == [25, 25, 25, 25]


def test_single_person():
    assert split_bill(999, 1) == [999]
''',
        },
        hidden='''from src.money import split_bill


def test_shares_always_add_up():
    for total in (100, 101, 7, 1, 1000003):
        for people in (2, 3, 7):
            assert sum(split_bill(total, people)) == total


def test_remainder_is_spread_by_one_cent():
    assert sorted(split_bill(100, 3)) == [33, 33, 34]
''',
        why="the remainder is discarded, so money disappears",
    ),
    Task(
        name="retry",
        prompt=(
            "We call an upstream service that sometimes fails before succeeding. "
            "It is configured for three attempts, but a call that fails twice and "
            "would succeed on the third still raises. Please fix it."
        ),
        files={
            "src/retry.py": '''"""Retrying a call that may fail transiently."""


def retry(fn, attempts=3):
    """Call `fn` until it succeeds, up to `attempts` times."""
    last = None
    for _ in range(attempts - 1):
        try:
            return fn()
        except Exception as exc:
            last = exc
    raise last
''',
            "tests/test_retry.py": '''import pytest

from src.retry import retry


def test_succeeds_first_time():
    assert retry(lambda: 7) == 7


def test_succeeds_on_second_attempt():
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 2:
            raise ValueError("not yet")
        return "ok"

    assert retry(flaky) == "ok"
''',
        },
        hidden='''import pytest

from src.retry import retry


def test_uses_every_attempt():
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("not yet")
        return "ok"

    assert retry(flaky) == "ok"
    assert len(calls) == 3


def test_gives_up_after_the_last_attempt():
    calls = []

    def always():
        calls.append(1)
        raise ValueError("no")

    with pytest.raises(ValueError):
        retry(always)
    assert len(calls) == 3
''',
        why="the loop runs attempts-1 times, so the configured last attempt never happens",
    ),
    Task(
        name="memoize",
        prompt=(
            "A cached lookup is returning stale answers. Calling the same function "
            "with the same positional argument but a different keyword argument "
            "gives back the earlier result. Please fix it."
        ),
        files={
            "src/cache.py": '''"""A small memoisation decorator."""

import functools


def memoize(fn):
    cache = {}

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        key = args
        if key not in cache:
            cache[key] = fn(*args, **kwargs)
        return cache[key]

    wrapper.cache = cache
    return wrapper
''',
            "tests/test_cache.py": '''from src.cache import memoize


def test_caches_by_argument():
    calls = []

    @memoize
    def double(n):
        calls.append(n)
        return n * 2

    assert double(2) == 4
    assert double(2) == 4
    assert calls == [2]
''',
        },
        hidden='''from src.cache import memoize


def test_keyword_arguments_are_part_of_the_key():
    @memoize
    def scale(n, factor=2):
        return n * factor

    assert scale(3) == 6
    assert scale(3, factor=10) == 30


def test_keyword_results_are_still_cached():
    calls = []

    @memoize
    def scale(n, factor=2):
        calls.append((n, factor))
        return n * factor

    scale(3, factor=10)
    scale(3, factor=10)
    assert len(calls) == 1
''',
        why="the cache key ignores kwargs, so different calls collide",
    ),
    Task(
        name="unique",
        prompt=(
            "Deduplicating a list is reordering it. The output should keep items in "
            "the order they were first seen. Please fix it."
        ),
        files={
            "src/dedupe.py": '''"""Removing duplicates from a sequence."""


def unique(items):
    """The distinct items, in the order they first appeared."""
    return sorted(set(items))
''',
            "tests/test_dedupe.py": '''from src.dedupe import unique


def test_removes_duplicates():
    assert unique([1, 1, 2, 3, 3]) == [1, 2, 3]


def test_empty():
    assert unique([]) == []
''',
        },
        hidden='''from src.dedupe import unique


def test_keeps_first_seen_order():
    assert unique([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_works_on_strings():
    assert unique(["b", "a", "b", "c"]) == ["b", "a", "c"]
''',
        why="sorted(set(...)) passes any test whose input is already sorted",
    ),
    Task(
        name="truncate",
        prompt=(
            "Our fixed-width table is overflowing. truncate(text, limit) sometimes "
            "returns a string longer than limit. Please fix it."
        ),
        files={
            "src/text.py": '''"""Shortening text for display."""

ELLIPSIS = "..."


def truncate(text, limit):
    """`text`, no longer than `limit` characters."""
    if len(text) <= limit:
        return text
    return text[:limit] + ELLIPSIS
''',
            "tests/test_text.py": '''from src.text import truncate


def test_short_text_is_unchanged():
    assert truncate("hello", 10) == "hello"


def test_long_text_is_shortened():
    assert truncate("hello world", 5).startswith("hello")
''',
        },
        hidden='''from src.text import truncate


def test_never_exceeds_the_limit():
    for limit in range(1, 12):
        assert len(truncate("hello world, this is long", limit)) <= limit


def test_exact_length_is_unchanged():
    assert truncate("hello", 5) == "hello"
''',
        why="the ellipsis is added after slicing to the limit, not within it",
    ),
    Task(
        name="csv_quotes",
        prompt=(
            "Importing a CSV export splits some rows into too many columns. It "
            "happens on rows where a field contains a comma. Please fix it."
        ),
        files={
            "src/csvline.py": '''"""Reading one line of a comma-separated file."""


def parse_line(line):
    """The fields in `line`."""
    return [field.strip() for field in line.rstrip("\\n").split(",")]
''',
            "tests/test_csvline.py": '''from src.csvline import parse_line


def test_plain_row():
    assert parse_line("a,b,c") == ["a", "b", "c"]


def test_trailing_newline():
    assert parse_line("a,b\\n") == ["a", "b"]
''',
        },
        hidden='''from src.csvline import parse_line


def test_quoted_field_containing_a_comma():
    assert parse_line('a,"b,c",d') == ["a", "b,c", "d"]


def test_quoted_field_at_the_end():
    assert parse_line('x,"y,z"') == ["x", "y,z"]
''',
        why="splitting on commas cannot respect quoting",
    ),
    Task(
        name="business_days",
        prompt=(
            "Our delivery estimates are a day early over a weekend. The business-day "
            "counter appears to be counting a weekend day as a working day. "
            "Please fix it."
        ),
        files={
            "src/calendar_days.py": '''"""Counting working days."""

from datetime import timedelta


def business_days(start, end):
    """Working days from `start` up to but not including `end`."""
    total = 0
    current = start
    while current < end:
        if current.weekday() <= 5:
            total += 1
        current += timedelta(days=1)
    return total
''',
            "tests/test_calendar_days.py": '''from datetime import date

from src.calendar_days import business_days


def test_midweek_range():
    assert business_days(date(2026, 9, 7), date(2026, 9, 10)) == 3


def test_empty_range():
    assert business_days(date(2026, 9, 7), date(2026, 9, 7)) == 0
''',
        },
        hidden='''from datetime import date

from src.calendar_days import business_days


def test_weekend_is_not_counted():
    # Friday to the following Monday: one working day, the Friday.
    assert business_days(date(2026, 9, 11), date(2026, 9, 14)) == 1


def test_full_week():
    assert business_days(date(2026, 9, 7), date(2026, 9, 14)) == 5
''',
        why="weekday() <= 5 includes Saturday, which no midweek test can see",
    ),
]


# The simple suite measured nothing useful: a plain agent resolved seven of the
# eight, leaving one discordant pair between the arms and no room for an effect
# to show. These are built for headroom instead. Each reports one symptom and
# hides a trap: the obvious fix addresses the reported case and leaves a closely
# related one broken, which is exactly the situation where an agent stops and
# says it is done.
HARD: list[Task] = [
    Task(
        name="merge_busy",
        prompt=(
            "Two meetings that touch end-to-start, one finishing at 11 and the next "
            "starting at 11, are shown as two separate busy periods instead of one. "
            "Please fix it."
        ),
        files={
            "src/intervals.py": '''"""Combining busy periods into the fewest possible blocks.

Overlapping or touching periods become one block. The result is ordered.
"""


def merge(periods):
    """The given periods, combined."""
    out = []
    for start, end in periods:
        if out and start < out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], end))
        else:
            out.append((start, end))
    return out
''',
            "tests/test_intervals.py": '''from src.intervals import merge


def test_overlapping_periods_combine():
    assert merge([(9, 11), (10, 12)]) == [(9, 12)]


def test_separate_periods_stay_separate():
    assert merge([(9, 10), (14, 15)]) == [(9, 10), (14, 15)]
''',
        },
        hidden='''from src.intervals import merge


def test_touching_periods_combine():
    assert merge([(9, 11), (11, 12)]) == [(9, 12)]


def test_input_order_does_not_matter():
    assert merge([(14, 15), (9, 11), (10, 12)]) == [(9, 12), (14, 15)]


def test_a_period_inside_another_is_absorbed():
    assert merge([(9, 17), (10, 11)]) == [(9, 17)]
''',
        why="changing < to <= fixes the reported case and leaves unsorted input broken",
    ),
    Task(
        name="slugify",
        prompt=(
            "Article titles containing punctuation are producing URLs with runs of "
            "hyphens in them, like 'what-s-new--really'. Please fix it."
        ),
        files={
            "src/slug.py": '''"""Turning a title into a URL slug.

A slug is lowercase, uses single hyphens between words, and has no hyphen at
either end.
"""

import re


def slugify(title):
    """A URL-safe form of `title`."""
    return re.sub(r"[^a-z0-9]", "-", title.lower())
''',
            "tests/test_slug.py": '''from src.slug import slugify


def test_simple_title():
    assert slugify("Hello World") == "hello-world"


def test_numbers_are_kept():
    assert slugify("Top 10") == "top-10"
''',
        },
        hidden='''from src.slug import slugify


def test_runs_of_punctuation_collapse():
    assert slugify("What's new -- really?") == "what-s-new-really"


def test_no_hyphen_at_either_end():
    assert slugify("...Hello...") == "hello"


def test_punctuation_only_title():
    assert slugify("!!!") == ""
''',
        why="collapsing runs still leaves the leading and trailing hyphens",
    ),
    Task(
        name="burst_limit",
        prompt=(
            "After a quiet period, a client can fire far more requests in a row than "
            "the configured burst allows. Please fix it."
        ),
        files={
            "src/limiter.py": '''"""A token-bucket rate limiter.

The bucket holds at most `capacity` tokens and refills at `per_second`. Each
allowed request costs one token.
"""


class RateLimiter:
    def __init__(self, capacity, per_second):
        self.capacity = capacity
        self.per_second = per_second
        self.tokens = float(capacity)
        self.updated = 0.0

    def allow(self, now):
        """Whether a request at time `now` is permitted."""
        self.tokens += (now - self.updated) * self.per_second
        self.updated = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
''',
            "tests/test_limiter.py": '''from src.limiter import RateLimiter


def test_burst_then_refusal():
    limiter = RateLimiter(capacity=2, per_second=1)
    assert limiter.allow(0)
    assert limiter.allow(0)
    assert not limiter.allow(0)


def test_refills_over_time():
    limiter = RateLimiter(capacity=2, per_second=1)
    limiter.allow(0)
    limiter.allow(0)
    assert limiter.allow(1)
''',
        },
        hidden='''from src.limiter import RateLimiter


def test_idle_time_does_not_grant_more_than_the_burst():
    limiter = RateLimiter(capacity=3, per_second=1)
    allowed = sum(1 for _ in range(100) if limiter.allow(1000))
    assert allowed == 3


def test_still_refills_after_being_capped():
    limiter = RateLimiter(capacity=3, per_second=1)
    for _ in range(100):
        limiter.allow(1000)
    assert limiter.allow(1002)
''',
        why="capping the bucket is easy to do in a way that also stops it refilling",
    ),
    Task(
        name="percentile",
        prompt=(
            "Asking for the 100th percentile raises an IndexError. Please fix it."
        ),
        files={
            "src/stats.py": '''"""Percentiles over a list of numbers.

The caller's list is left untouched.
"""


def percentile(values, p):
    """The value at percentile `p`, between 0 and 100."""
    values.sort()
    index = int(len(values) * p / 100)
    return values[index]
''',
            "tests/test_stats.py": '''from src.stats import percentile


def test_median_of_odd_length():
    assert percentile([3, 1, 2], 50) == 2


def test_low_percentile():
    assert percentile([10, 20, 30, 40], 0) == 10
''',
        },
        hidden='''from src.stats import percentile


def test_top_percentile_is_the_maximum():
    assert percentile([3, 1, 2], 100) == 3


def test_the_callers_list_is_left_alone():
    values = [3, 1, 2]
    percentile(values, 50)
    assert values == [3, 1, 2]


def test_single_value():
    assert percentile([7], 100) == 7
''',
        why="clamping the index fixes the crash and leaves the caller's list reordered",
    ),
    Task(
        name="deep_merge",
        prompt=(
            "Loading a second config file is changing the defaults dictionary that "
            "was passed in, so later loads start from the wrong baseline. "
            "Please fix it."
        ),
        files={
            "src/config.py": '''"""Merging one configuration over another.

Neither argument is modified; the merged result is new.
"""


def deep_merge(base, override):
    """`base` with `override` applied on top of it."""
    result = base
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
''',
            "tests/test_config.py": '''from src.config import deep_merge


def test_override_wins():
    assert deep_merge({"a": 1}, {"a": 2}) == {"a": 2}


def test_nested_values_merge():
    merged = deep_merge({"db": {"host": "x", "port": 1}}, {"db": {"port": 2}})
    assert merged == {"db": {"host": "x", "port": 2}}
''',
        },
        hidden='''from src.config import deep_merge


def test_the_base_is_not_modified():
    base = {"a": 1}
    deep_merge(base, {"a": 2})
    assert base == {"a": 1}


def test_nested_dictionaries_are_not_modified_either():
    base = {"db": {"host": "x", "port": 1}}
    deep_merge(base, {"db": {"port": 2}})
    assert base == {"db": {"host": "x", "port": 1}}


def test_the_override_is_not_modified():
    override = {"db": {"port": 2}}
    deep_merge({"db": {"host": "x"}}, override)
    assert override == {"db": {"port": 2}}
''',
        why="a shallow copy fixes the top level and leaves nested dicts shared",
    ),
    Task(
        name="word_wrap",
        prompt=(
            "Wrapping a paragraph that begins with a long URL produces an empty "
            "first line, and the URL sits on a line wider than the column. "
            "Please fix it."
        ),
        files={
            "src/wrap.py": '''"""Wrapping text to a column width.

No line exceeds `width`, and no line is empty. A word longer than `width` is
broken across lines.
"""


def wrap(text, width):
    """`text` laid out in lines of at most `width` characters."""
    lines, current = [], ""
    for word in text.split():
        if len(current) + len(word) + 1 > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines
''',
            "tests/test_wrap.py": '''from src.wrap import wrap


def test_short_text_is_one_line():
    assert wrap("hello world", 20) == ["hello world"]


def test_wraps_at_the_column():
    assert wrap("one two three four", 9) == ["one two", "three", "four"]
''',
        },
        hidden='''from src.wrap import wrap

LONG = "https://example.com/a/very/long/path/that/will/not/fit is the link"


def test_no_line_is_empty():
    assert all(line for line in wrap(LONG, 20))


def test_no_line_exceeds_the_width():
    assert all(len(line) <= 20 for line in wrap(LONG, 20))


def test_no_characters_are_lost():
    joined = "".join(wrap(LONG, 20)).replace(" ", "")
    assert joined == LONG.replace(" ", "")
''',
        why="removing the empty line is the obvious fix and leaves the long word overflowing",
    ),
    Task(
        name="version_compare",
        prompt=(
            "Our updater thinks 1.2 and 1.2.0 are different versions and keeps "
            "offering an upgrade that is already installed. Please fix it."
        ),
        files={
            "src/version.py": '''"""Comparing dotted version strings.

Returns -1, 0 or 1. Trailing zero components do not change a version.
"""


def compare(a, b):
    """-1 if a < b, 0 if equal, 1 if a > b."""
    left = [int(part) for part in a.split(".")]
    right = [int(part) for part in b.split(".")]
    return (left > right) - (left < right)
''',
            "tests/test_version.py": '''from src.version import compare


def test_same_length():
    assert compare("1.2.3", "1.2.4") == -1
    assert compare("2.0.0", "1.9.9") == 1


def test_identical():
    assert compare("1.2.3", "1.2.3") == 0
''',
        },
        hidden='''from src.version import compare


def test_trailing_zeros_do_not_matter():
    assert compare("1.2", "1.2.0") == 0
    assert compare("1.2.0.0", "1.2") == 0


def test_shorter_version_can_still_be_smaller():
    assert compare("1.2", "1.2.1") == -1


def test_numeric_not_lexical():
    assert compare("1.10", "1.9") == 1
''',
        why="padding one side is easy to get right in one direction only",
    ),
    Task(
        name="csv_write",
        prompt=(
            "Rows we export containing a quotation mark cannot be read back in by "
            "the importer. Please fix it."
        ),
        files={
            "src/csvout.py": '''"""Writing one row of a comma-separated file.

The output must be readable by any standard CSV reader.
"""


def write_line(fields):
    """`fields` as a single CSV row, without a trailing newline."""
    return ",".join(f'"{field}"' if "," in field else field for field in fields)
''',
            "tests/test_csvout.py": '''from src.csvout import write_line


def test_plain_row():
    assert write_line(["a", "b"]) == "a,b"


def test_field_with_a_comma_is_quoted():
    assert write_line(["a", "b,c"]) == 'a,"b,c"'
''',
        },
        hidden='''import csv
import io

from src.csvout import write_line

ROWS = [
    ["a", 'say "hi"'],
    ["a", 'b,"c"'],
    ['"'],
    ["plain", "row"],
]


def test_every_row_reads_back_unchanged():
    for fields in ROWS:
        line = write_line(fields)
        assert next(csv.reader(io.StringIO(line))) == fields
''',
        why="escaping the quote is not enough; a field containing one must also be quoted",
    ),
]

from .mined import load as _load_mined
from .tasks_repo import EASY, REPO

SUITES: dict[str, list[Task]] = {
    "mined": _load_mined(),
    "simple": TASKS,
    "hard": HARD + EASY,
    "repo": REPO,
    "all": TASKS + HARD + EASY,
    "every": TASKS + HARD + EASY + REPO + _load_mined(),
}


def by_name(name: str) -> Task:
    for task in SUITES["every"]:
        if task.name == name:
            return task
    raise KeyError(name)
