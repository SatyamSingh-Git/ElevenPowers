"""The box office over one data directory, with every service wired to the same clock."""
from pathlib import Path

from ..config import load_settings
from ..errors import BoxOfficeError
from ..storage.customers import CustomerBook
from ..storage.jsonstore import Store
from ..storage.ledger import Ledger
from .availability import seat_states
from .checks import check_data
from .holds import HoldService
from .refunds import RefundService
from .sales import SalesService
from .schedule import ScheduleService
from .waitlist import Waitlist


class BoxOffice:
    def __init__(self, root, clock):
        self.root = Path(root)
        self.clock = clock
        self.settings = load_settings(self.root)
        self.store = Store(self.root)
        self.ledger = Ledger(self.root)
        self.customers = CustomerBook(self.root)
        self.schedule = ScheduleService(self.store)
        self.holds = HoldService(self.store, clock, self.settings)
        self.sales = SalesService(self.store, self.holds, self.customers, self.ledger, clock, self.settings)
        self.refunds = RefundService(self.store, self.ledger, clock, self.settings)
        self.waitlist = Waitlist(self.store, clock)

    def seat_states(self, code):
        return seat_states(self.store, code, self.clock.now())

    def order(self, order_id):
        order = self.store.load_orders().get(order_id)
        if order is None:
            raise BoxOfficeError("unknown-order", order=order_id)
        return order

    def check(self):
        return check_data(self.store)
