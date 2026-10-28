from dataclasses import replace
from datetime import date, datetime

import pytest

from parcelpost.core.errors import ScanError
from parcelpost.formats.events import Event, append_events, latest_by_number, read_events
from parcelpost.formats.scanfile import parse_scan_file
from parcelpost.reports.daily import daily_summary, render_daily
from parcelpost.reports.stalled import find_stalled
from parcelpost.services.booking import book
from parcelpost.services.scans import import_scans
from parcelpost.services.tracking import track
from parcelpost.storage.shipments import ShipmentStore

HEADER = "tracking_number,code,date,time,depot\n"


def test_parse_scan_file():
    rows = parse_scan_file(HEADER + "pp000000019gb,pu,2026-03-02,18:05,bhx\n\n")
    assert len(rows) == 1
    assert rows[0].tracking_number == "PP000000019GB"
    assert rows[0].code == "PU"
    assert rows[0].at == datetime(2026, 3, 2, 18, 5)
    assert rows[0].line == 2


def test_scan_file_needs_its_header():
    with pytest.raises(ScanError, match="scan file must start with the header"):
        parse_scan_file("number,code\n")


def test_scan_file_bad_time():
    with pytest.raises(ScanError, match="line 2: invalid date or time 2026-03-02 25:00"):
        parse_scan_file(HEADER + "PP000000019GB,PU,2026-03-02,25:00,BHX\n")


def test_malformed_numbers_are_refused(settings, clock, make_order):
    book(settings, make_order(), clock=clock)
    with pytest.raises(ScanError, match="line 2: invalid tracking number PP12GB"):
        import_scans(settings, HEADER + "PP12GB,PU,2026-03-02,18:05,BHX\n")
    assert read_events(settings.events_path) == []


def _record(settings, shipment, *scans):
    append_events(settings.events_path,
                  [Event(shipment.tracking_number, code, at, "BHX") for code, at in scans])
    store = ShipmentStore(settings.store_path)
    store.get(shipment.tracking_number).status = "in_transit"
    store.save()


def test_events_round_trip_and_latest(settings, clock, make_order):
    shipment = book(settings, make_order(), clock=clock)
    _record(settings, shipment, ("PU", datetime(2026, 3, 2, 18, 0)), ("AR", datetime(2026, 3, 3, 2, 0)))
    events = read_events(settings.events_path)
    assert [event.code for event in events] == ["PU", "AR"]
    assert latest_by_number(events)[shipment.tracking_number].code == "AR"


def test_track_lists_scans_in_time_order(settings, clock, make_order):
    shipment = book(settings, make_order(), clock=clock)
    _record(settings, shipment, ("AR", datetime(2026, 3, 3, 2, 0)), ("PU", datetime(2026, 3, 2, 18, 0)))
    tracking = track(settings, shipment.tracking_number.lower())
    assert [event.code for event in tracking.events] == ["PU", "AR"]
    assert tracking.status == "in_transit"
    assert not tracking.late_on(date(2026, 3, 5))
    assert tracking.late_on(date(2026, 3, 6))


def test_stalled_after_stale_hours(settings, clock, make_order):
    quiet = book(settings, make_order(), clock=clock)
    busy = book(settings, make_order(account="BOLT"), clock=clock)
    _record(settings, quiet, ("PU", datetime(2026, 3, 2, 18, 0)))
    _record(settings, busy, ("PU", datetime(2026, 3, 4, 18, 0)))
    stalled = find_stalled(settings, datetime(2026, 3, 5, 12, 0))
    assert [row.tracking_number for row in stalled] == [quiet.tracking_number]
    assert stalled[0].hours == 66
    assert find_stalled(replace(settings, stale_hours=72), datetime(2026, 3, 5, 12, 0)) == []


def test_daily_summary(settings, clock, make_order):
    book(settings, make_order(), clock=clock)
    book(settings, make_order(account="BOLT", service="express", weight_grams=1000), clock=clock)
    summary = daily_summary(settings, date(2026, 3, 2))
    assert summary.shipments == 2
    assert summary.weight_grams == 3500
    assert summary.by_status["booked"] == 2
    assert "Express" in render_daily(summary)


def test_daily_summary_for_a_quiet_day(settings):
    summary = daily_summary(settings, date(2026, 3, 2))
    assert render_daily(summary) == "Nothing collected on 2026-03-02."
