import json

from boxoffice.reports.cashup import cashup
from boxoffice.reports.daily import COLUMNS, daily_takings, totals
from boxoffice.reports.formatters import Column, render
from boxoffice.reports.occupancy import occupancy
from boxoffice.reports.price_list import price_list
from boxoffice.reports.seatplan import render_seatplan
from boxoffice.storage.seatmap_format import parse_seatmap

from conftest import SEATMAP

ENTRIES = [
    {"kind": "sale", "date": "2026-05-01", "tickets": 2, "amount": 6150, "payment": "card"},
    {"kind": "sale", "date": "2026-05-02", "tickets": 1, "amount": 2150, "payment": "cash"},
    {"kind": "refund", "date": "2026-05-02", "tickets": 1, "amount": -3000, "payment": "card"},
]


def test_daily_takings():
    assert daily_takings(ENTRIES) == [
        {"day": "2026-05-01", "sold": 2, "returned": 0, "sales": 6150, "refunds": 0, "net": 6150},
        {"day": "2026-05-02", "sold": 1, "returned": 1, "sales": 2150, "refunds": 3000, "net": -850},
    ]
    assert [row["day"] for row in daily_takings(ENTRIES, "2026-05-02")] == ["2026-05-02"]
    assert totals(daily_takings(ENTRIES))["net"] == 5300


def test_daily_text_table():
    text = render(COLUMNS, daily_takings(ENTRIES[:1]))
    assert text.splitlines() == [
        "day         sold  returned  sales  refunds    net",
        "----------  ----  --------  -----  -------  -----",
        "2026-05-01     2         0  61.50     0.00  61.50",
    ]


def test_cashup_lists_every_method():
    rows = cashup(ENTRIES[1:])
    assert rows == [
        {"payment": "card", "entries": 1, "amount": -3000},
        {"payment": "cash", "entries": 1, "amount": 2150},
        {"payment": "total", "entries": 2, "amount": -850},
    ]


def test_formats():
    columns = [Column("name"), Column("price", "money")]
    rows = [{"name": "a", "price": 150}]
    assert render(columns, rows, "csv") == "name,price\na,1.50"
    assert json.loads(render(columns, rows, "json")) == rows
    assert render(columns, rows, "markdown").splitlines()[1] == "|---|---:|"


def test_seatplan():
    venue = parse_seatmap(SEATMAP)
    states = {seat.id: "free" for seat in venue.seats()}
    states.update({"A1": "sold", "A2": "held"})
    lines = render_seatplan(venue, states).splitlines()
    assert lines[2] == "  A    1 x h . . . ."
    assert lines[-1] == "key: . free  h held  x sold"


def test_price_list(office):
    columns, rows = price_list(office.store.performance("TEMP-0520"), office.store.venue())
    assert [column.name for column in columns] == ["tier", "adult", "child", "senior", "student"]
    assert rows[0] == {"tier": "A", "adult": 3000, "child": 1500, "senior": 2400, "student": 2250}


def test_occupancy(office):
    office.sales.checkout(office.holds.place("TEMP-0520", ["A1", "C1"]).id)
    rows = occupancy(office.store.venue(), office.store.load_orders(), "TEMP-0520")
    assert rows == [
        {"section": "Stalls", "capacity": 12, "sold": 1, "occupancy": 8.3},
        {"section": "Circle", "capacity": 4, "sold": 1, "occupancy": 25.0},
        {"section": "all", "capacity": 16, "sold": 2, "occupancy": 12.5},
    ]
