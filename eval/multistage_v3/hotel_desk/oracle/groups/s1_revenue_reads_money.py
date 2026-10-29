"""Stage 1: the revenue report reads a journal whose amounts are written as 0.00."""
from datetime import date

from hoteldesk.reports.revenue import revenue_summary, revenue_text

JOURNAL = (
    "business_date,rooms_sold,rooms_available,room_revenue,tax_revenue,other_revenue,payments\n"
    "2026-03-02,2,5,380.00,44.65,12.00,0.00\n"
    "2026-03-03,1,5,120.00,14.10,0.00,581.10\n"
    "2026-03-04,3,5,410.50,48.23,7.25,100.00\n"
)


def test_revenue_summary_reads_money_columns(tmp_path):
    journal = tmp_path / "audit_journal.csv"
    journal.write_text(JOURNAL, encoding="utf-8")
    summary = revenue_summary(journal)
    assert [day["room_revenue"] for day in summary["days"]] == [38000, 12000, 41050]
    totals = summary["totals"]
    assert totals["room_revenue"] == 91050
    assert totals["tax_revenue"] == 10698
    assert totals["other_revenue"] == 1925
    assert totals["payments"] == 68110
    assert totals["rooms_sold"] == 6
    assert totals["adr"] == 15175


def test_revenue_text_from_a_money_journal(tmp_path):
    journal = tmp_path / "audit_journal.csv"
    journal.write_text(JOURNAL, encoding="utf-8")
    text = revenue_text(revenue_summary(journal, date(2026, 3, 3), date(2026, 3, 4)))
    total = [line for line in text.splitlines() if line.startswith("total")]
    assert len(total) == 1
    assert "530.50" in total[0] and "62.33" in total[0] and "681.10" in total[0]
