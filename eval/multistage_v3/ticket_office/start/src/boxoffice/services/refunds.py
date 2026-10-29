"""Giving money back: refunds of some or all seats, and exchanges to another performance."""
from datetime import timedelta

from ..errors import BoxOfficeError
from ..model.concessions import concession_price
from ..model.order import OrderLine
from .availability import seat_states


class RefundService:
    def __init__(self, store, ledger, clock, settings):
        self.store = store
        self.ledger = ledger
        self.clock = clock
        self.settings = settings

    def refund(self, order_id, seats=None):
        """Refund the named seats of an order, or the whole order when `seats` is None.

        The booking fee is kept. Returns the amount paid back, in pence.
        """
        orders = self.store.load_orders()
        order = self._order(orders, order_id)
        now = self.clock.now()
        self._check_open(order.performance, now)
        if seats is None:
            lines = list(order.lines)
        else:
            lines = [self._line(order, seat) for seat in seats]
        amount = sum(line.price for line in lines)
        for line in lines:
            line.refunded = True
        self.store.save_orders(orders)
        self.ledger.record_entry("refund", at=now, order=order.id, performance=order.performance,
                                 tickets=len(lines), amount=-amount, payment=order.payment)
        return amount

    def exchange(self, order_id, code, seats):
        """Move every seat of an order to `seats` of performance `code`.

        Each new seat keeps the concession of the seat it replaces, taking the
        seats in seat-map order. Returns what the customer pays, in pence;
        negative when they are owed money back.
        """
        orders = self.store.load_orders()
        order = self._order(orders, order_id)
        if any(line.refunded for line in order.lines):
            raise BoxOfficeError("exchange-refunded", order=order_id)
        now = self.clock.now()
        self._check_open(order.performance, now)
        performance = self.store.performance(code)
        if performance.cancelled:
            raise BoxOfficeError("performance-cancelled", code=code)
        if performance.has_started(now):
            raise BoxOfficeError("performance-started", code=code)
        if len(seats) != len(order.lines):
            raise BoxOfficeError("seat-count", count=len(order.lines))
        venue = self.store.venue()
        states = seat_states(self.store, code, now)
        own = {line.seat for line in order.lines} if code == order.performance else set()
        seen = set()
        for seat in seats:
            if venue.seat(seat) is None:
                raise BoxOfficeError("unknown-seat", seat=seat)
            if seat in seen:
                raise BoxOfficeError("duplicate-seat", seat=seat)
            if states[seat] != "free" and seat not in own:
                raise BoxOfficeError("seat-unavailable", seat=seat)
            seen.add(seat)
        position = venue.seat_order()
        new_lines = []
        for old, seat in zip(order.lines, sorted(seats, key=position.__getitem__)):
            tier = venue.seat(seat).tier
            new_lines.append(OrderLine(seat, tier, old.concession,
                                       concession_price(performance.prices[tier], old.concession)))
        old_performance, old_value = order.performance, order.face_value
        order.performance, order.lines = code, new_lines
        self.store.save_orders(orders)
        self.ledger.record_entry("refund", at=now, order=order.id, performance=old_performance,
                                 tickets=len(new_lines), amount=-old_value, payment=order.payment)
        self.ledger.record_entry("sale", at=now, order=order.id, performance=code,
                                 tickets=len(new_lines), amount=order.face_value, payment=order.payment)
        return order.face_value - old_value

    def cancel_performance(self, code):
        """Cancel performance `code` and pay back every order for it in full, booking fee included.

        Returns how many orders were paid back and the total paid back, in pence.
        """
        performances = self.store.performances()
        performance = performances.get(code)
        if performance is None:
            raise BoxOfficeError("unknown-performance", code=code)
        if performance.cancelled:
            raise BoxOfficeError("performance-cancelled", code=code)
        now = self.clock.now()
        orders = self.store.load_orders()
        count, paid_back = 0, 0
        for order in orders.values():
            lines = order.active_lines()
            if order.performance != code or not lines:
                continue
            amount = sum(line.price for line in lines) + order.fee
            for line in lines:
                line.refunded = True
            self.ledger.record_entry("refund", at=now, order=order.id, performance=code,
                                     tickets=len(lines), amount=-amount, payment=order.payment)
            count += 1
            paid_back += amount
        performance.cancelled = True
        self.store.save_orders(orders)
        self.store.save_performances(performances)
        return count, paid_back

    def _order(self, orders, order_id):
        order = orders.get(order_id)
        if order is None:
            raise BoxOfficeError("unknown-order", order=order_id)
        return order

    def _line(self, order, seat):
        line = order.line_for(seat)
        if line is None:
            raise BoxOfficeError("not-in-order", seat=seat, order=order.id)
        return line

    def _check_open(self, code, now):
        hours = self.settings.refund_cutoff_hours
        if now > self.store.performance(code).starts - timedelta(hours=hours):
            raise BoxOfficeError("refund-closed", hours=hours)
