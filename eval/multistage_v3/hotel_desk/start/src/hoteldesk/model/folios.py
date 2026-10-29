"""A guest's folio: what they were charged and what they paid."""
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Charge:
    day: date
    code: str
    description: str
    amount: int


@dataclass
class Payment:
    day: date
    method: str
    amount: int


@dataclass
class Folio:
    reservation_id: str
    charges: list = field(default_factory=list)
    payments: list = field(default_factory=list)

    @property
    def charged(self):
        return sum(charge.amount for charge in self.charges)

    @property
    def paid(self):
        return sum(payment.amount for payment in self.payments)

    @property
    def balance(self):
        return self.charged - self.paid

    def charges_on(self, day):
        return [charge for charge in self.charges if charge.day == day]
