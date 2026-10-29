"""Holds on seats, and the orders they turn into."""
from dataclasses import dataclass
from datetime import datetime

from ..clock import format_time, parse_time


@dataclass
class Hold:
    """Seats set aside for a customer while they decide. A hold is never deleted:
    releasing it or selling it changes its status."""

    id: str
    performance: str
    seats: list
    placed: datetime
    expires: datetime
    status: str = "active"
    order: str | None = None

    def is_active(self, now):
        return self.status == "active" and now < self.expires

    def to_dict(self):
        return {"performance": self.performance, "seats": list(self.seats),
                "placed": format_time(self.placed), "expires": format_time(self.expires),
                "status": self.status, "order": self.order}

    @classmethod
    def from_dict(cls, hold_id, data):
        return cls(hold_id, data["performance"], list(data["seats"]), parse_time(data["placed"]),
                   parse_time(data["expires"]), data["status"], data["order"])


@dataclass
class OrderLine:
    seat: str
    tier: str
    concession: str
    price: int
    refunded: bool = False

    def to_dict(self):
        return {"seat": self.seat, "tier": self.tier, "concession": self.concession,
                "price": self.price, "refunded": self.refunded}

    @classmethod
    def from_dict(cls, data):
        return cls(data["seat"], data["tier"], data["concession"], data["price"], data["refunded"])


@dataclass
class Order:
    id: str
    performance: str
    lines: list
    fee: int
    payment: str
    created: datetime
    customer: str | None = None

    @property
    def face_value(self):
        return sum(line.price for line in self.lines)

    @property
    def total(self):
        return self.face_value + self.fee

    def active_lines(self):
        return [line for line in self.lines if not line.refunded]

    def line_for(self, seat):
        return next((line for line in self.lines if line.seat == seat), None)

    def to_dict(self):
        return {"performance": self.performance, "lines": [line.to_dict() for line in self.lines],
                "fee": self.fee, "payment": self.payment, "created": format_time(self.created),
                "customer": self.customer}

    @classmethod
    def from_dict(cls, order_id, data):
        return cls(order_id, data["performance"], [OrderLine.from_dict(line) for line in data["lines"]],
                   data["fee"], data["payment"], parse_time(data["created"]), data["customer"])
