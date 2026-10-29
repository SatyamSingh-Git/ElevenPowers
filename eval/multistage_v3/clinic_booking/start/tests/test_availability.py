from datetime import datetime

from clinicbook.services.availability import first_free, free_slots, free_slots_from
from conftest import MONDAY, SUNDAY, at

NOW = datetime(2026, 2, 27, 8, 0)


def test_slots_run_back_to_back_from_opening(clinic):
    slots = free_slots(clinic, [], MONDAY, NOW, practitioner="amy")
    assert [slot.start for slot in slots[:3]] == [at("09:00"), at("09:20"), at("09:40")]
    assert slots[-1].start == at("16:40")
    assert len(slots) == 24


def test_booked_slot_is_not_offered(clinic, desk):
    desk.book("amy", MONDAY, at("09:00"), "Ann Lee", "07700900001")
    starts = [slot.start for slot in free_slots(clinic, desk.bookings, MONDAY, NOW, practitioner="amy")]
    assert at("09:00") not in starts
    assert at("10:40") in starts


def test_nothing_on_closed_days_or_in_the_past(clinic):
    assert free_slots(clinic, [], SUNDAY, NOW) == []
    late = datetime(2026, 3, 2, 16, 30)
    assert [slot.start for slot in free_slots(clinic, [], MONDAY, late, practitioner="amy")] == [at("16:40")]


def test_slots_across_days_and_first_free(clinic):
    slots = free_slots_from(clinic, [], MONDAY, 2, NOW, practitioner="cara")
    assert {slot.day.isoformat() for slot in slots} == {"2026-03-03"}
    slot = first_free(clinic, [], MONDAY, 7, NOW)
    assert (slot.day, slot.start) == (MONDAY, at("09:00"))
