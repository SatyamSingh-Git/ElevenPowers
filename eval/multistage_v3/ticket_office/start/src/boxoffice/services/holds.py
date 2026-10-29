"""Holding seats for a customer while they decide, for `hold_minutes` at most."""
from datetime import timedelta

from ..errors import BoxOfficeError
from ..model.order import Hold
from .availability import best_available, seat_states


class HoldService:
    def __init__(self, store, clock, settings):
        self.store = store
        self.clock = clock
        self.settings = settings

    def place(self, code, seats):
        """Hold the named seats of performance `code`; they come back in seat-map order."""
        now = self.clock.now()
        performance = self.store.performance(code)
        if performance.cancelled:
            raise BoxOfficeError("performance-cancelled", code=code)
        if performance.has_started(now):
            raise BoxOfficeError("performance-started", code=code)
        if not seats:
            raise BoxOfficeError("no-seats")
        limit = self.settings.max_tickets_per_order
        if len(seats) > limit:
            raise BoxOfficeError("too-many", limit=limit)
        venue = self.store.venue()
        states = seat_states(self.store, code, now)
        seen = set()
        for seat in seats:
            if venue.seat(seat) is None:
                raise BoxOfficeError("unknown-seat", seat=seat)
            if seat in seen:
                raise BoxOfficeError("duplicate-seat", seat=seat)
            if states[seat] != "free":
                raise BoxOfficeError("seat-unavailable", seat=seat)
            seen.add(seat)
        order = venue.seat_order()
        holds = self.store.load_holds()
        hold = Hold(self.store.new_hold_id(holds), code, sorted(seats, key=order.__getitem__), now,
                    now + timedelta(minutes=self.settings.hold_minutes))
        holds[hold.id] = hold
        self.store.save_holds(holds)
        return hold

    def place_best(self, code, count, section=None):
        """Hold the best `count` seats side by side, optionally within one section."""
        limit = self.settings.max_tickets_per_order
        if count > limit:
            raise BoxOfficeError("too-many", limit=limit)
        seats = best_available(self.store, code, count, self.clock.now(), section)
        return self.place(code, seats)

    def active(self, hold_id):
        """The hold `hold_id`, provided it can still be sold."""
        hold = self.store.load_holds().get(hold_id)
        if hold is None:
            raise BoxOfficeError("unknown-hold", hold=hold_id)
        if hold.status != "active":
            raise BoxOfficeError("hold-closed", hold=hold_id)
        if not hold.is_active(self.clock.now()):
            raise BoxOfficeError("hold-expired", hold=hold_id)
        return hold

    def release(self, hold_id):
        self.active(hold_id)
        holds = self.store.load_holds()
        holds[hold_id].status = "released"
        self.store.save_holds(holds)
        return holds[hold_id]

    def mark_sold(self, hold_id, order_id):
        holds = self.store.load_holds()
        holds[hold_id].status = "sold"
        holds[hold_id].order = order_id
        self.store.save_holds(holds)
