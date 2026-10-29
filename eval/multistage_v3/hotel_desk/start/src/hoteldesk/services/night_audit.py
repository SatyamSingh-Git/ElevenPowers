"""The night audit closes the business date.

It posts each in-house guest's room charge for the night, marks guests who never
arrived as no-shows, writes the day's line to the audit journal and moves the
business date on by one day.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta

from ..model.charges import ROOM, TAX
from ..model.reservations import BOOKED, IN_HOUSE, NO_SHOW
from ..model.rooms import DIRTY
from ..storage import journal
from . import billing, inventory, pricing


@dataclass
class AuditResult:
    business_date: date
    room_charges: list = field(default_factory=list)
    no_shows: list = field(default_factory=list)
    extended: list = field(default_factory=list)
    statistics: dict = field(default_factory=dict)
    room_revenue: int = 0
    tax_revenue: int = 0
    other_revenue: int = 0
    payments: int = 0


def open_items(hotel):
    """Things the auditor should look at before closing the day; none of them stops the audit."""
    day = hotel.business_date
    items = []
    for reservation in sorted(hotel.reservations.values(), key=lambda r: r.id):
        if reservation.status == BOOKED and reservation.arrival == day:
            items.append(f"{reservation.id} {reservation.guest} has not arrived and will be a no-show")
        elif reservation.status == IN_HOUSE and reservation.departure == day:
            items.append(f"{reservation.id} {reservation.guest} was due out today and will be extended")
    for room in sorted(hotel.rooms.values(), key=lambda room: room.number):
        if not room.occupied and room.status == DIRTY:
            items.append(f"Room {room.number} is vacant and still dirty")
    return items


def _extend(hotel, settings, reservation):
    """A guest still in house on their departure date stays one more night at the going rate."""
    night = reservation.departure
    reservation.departure = night + timedelta(days=1)
    reservation.rates.extend(pricing.nightly_rates(hotel, settings, reservation.room_type,
                                                   reservation.rate_plan, night, reservation.departure))


def _post_room_charges(hotel, settings, day, result):
    for reservation in sorted(hotel.reservations_with(IN_HOUSE), key=lambda r: r.room):
        if reservation.departure == day:
            _extend(hotel, settings, reservation)
            result.extended.append(reservation.id)
        rate = reservation.rate_for(day)
        billing.post_charge(hotel, reservation.id, ROOM, rate, f"Room {reservation.room} night of {day.isoformat()}")
        result.room_charges.append((reservation.id, reservation.room, rate))


def _mark_no_shows(hotel, day, result):
    for reservation in hotel.reservations_with(BOOKED):
        if reservation.arrival == day:
            reservation.status = NO_SHOW
            result.no_shows.append(reservation.id)


def _total_the_day(hotel, day, result):
    for folio in hotel.folios.values():
        for charge in folio.charges_on(day):
            if charge.code == ROOM:
                result.room_revenue += charge.amount
            elif charge.code == TAX:
                result.tax_revenue += charge.amount
            else:
                result.other_revenue += charge.amount
        result.payments += sum(payment.amount for payment in folio.payments if payment.day == day)


def run_audit(hotel, settings, journal_path=None):
    day = hotel.business_date
    result = AuditResult(day)
    _post_room_charges(hotel, settings, day, result)
    _mark_no_shows(hotel, day, result)
    result.statistics = inventory.day_statistics(hotel, day)
    _total_the_day(hotel, day, result)
    if journal_path is not None:
        journal.append_entry(journal_path, {
            "business_date": day,
            "rooms_sold": result.statistics["sold"],
            "rooms_available": result.statistics["available"],
            "room_revenue": result.room_revenue,
            "tax_revenue": result.tax_revenue,
            "other_revenue": result.other_revenue,
            "payments": result.payments,
        })
    hotel.business_date = day + timedelta(days=1)
    return result
