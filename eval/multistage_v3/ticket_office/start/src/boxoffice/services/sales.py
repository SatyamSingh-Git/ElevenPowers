"""Turning a hold into an order: pricing each seat, taking payment, recording the sale."""
from ..errors import BoxOfficeError
from ..model.concessions import concession_price
from ..model.order import Order, OrderLine

PAYMENT_METHODS = ("card", "cash")


class SalesService:
    def __init__(self, store, holds, customers, ledger, clock, settings):
        self.store = store
        self.holds = holds
        self.customers = customers
        self.ledger = ledger
        self.clock = clock
        self.settings = settings

    def checkout(self, hold_id, concessions=None, payment="card", customer=None):
        """Sell the seats of hold `hold_id`.

        `concessions` maps a seat to its concession; seats not named are adult.
        `customer` is the email of someone in the customer book, if they gave one.
        The order is charged the booking fee once, whatever the number of seats.
        """
        concessions = concessions or {}
        if payment not in PAYMENT_METHODS:
            raise BoxOfficeError("unknown-payment", name=payment)
        if customer is not None:
            customer = self.customers.get(customer).email
        hold = self.holds.active(hold_id)
        for seat in concessions:
            if seat not in hold.seats:
                raise BoxOfficeError("not-in-hold", seat=seat, hold=hold_id)
        performance = self.store.performance(hold.performance)
        venue = self.store.venue()
        lines = []
        for seat_id in hold.seats:
            tier = venue.seat(seat_id).tier
            name = concessions.get(seat_id, "adult")
            lines.append(OrderLine(seat_id, tier, name, concession_price(performance.prices[tier], name)))
        now = self.clock.now()
        orders = self.store.load_orders()
        order = Order(self.store.new_order_id(orders), performance.code, lines,
                      self.settings.booking_fee, payment, now, customer)
        orders[order.id] = order
        self.store.save_orders(orders)
        self.holds.mark_sold(hold_id, order.id)
        self.ledger.record_entry("sale", at=now, order=order.id, performance=order.performance,
                                 tickets=len(lines), amount=order.total, payment=payment)
        return order

    def assign_customer(self, order_id, customer):
        """Record who an order belongs to, or with None that it belongs to nobody in the book."""
        orders = self.store.load_orders()
        order = orders.get(order_id)
        if order is None:
            raise BoxOfficeError("unknown-order", order=order_id)
        order.customer = None if customer is None else self.customers.get(customer).email
        self.store.save_orders(orders)
        return order
