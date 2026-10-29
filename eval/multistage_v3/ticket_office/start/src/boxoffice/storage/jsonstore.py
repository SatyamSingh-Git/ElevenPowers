"""The data directory: the venue, performances, holds and orders, one file each."""
import json
from pathlib import Path

from ..errors import BoxOfficeError
from ..model.order import Hold, Order
from ..model.performance import Performance
from .seatmap_format import parse_seatmap

VENUE_FILE = "venue.txt"
PERFORMANCES_FILE = "performances.json"
HOLDS_FILE = "holds.json"
ORDERS_FILE = "orders.json"
WAITLIST_FILE = "waitlist.json"


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self._venue = None

    def venue(self):
        if self._venue is None:
            path = self.root / VENUE_FILE
            if not path.is_file():
                raise BoxOfficeError("no-venue")
            self._venue = parse_seatmap(path.read_text(encoding="utf-8"))
        return self._venue

    def install_venue(self, text):
        venue = parse_seatmap(text)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / VENUE_FILE).write_text(text, encoding="utf-8")
        self._venue = venue
        return venue

    def performances(self):
        return {data["code"]: Performance.from_dict(data) for data in self._read(PERFORMANCES_FILE, [])}

    def performance(self, code):
        found = self.performances().get(code)
        if found is None:
            raise BoxOfficeError("unknown-performance", code=code)
        return found

    def save_performances(self, performances):
        ordered = sorted(performances.values(), key=lambda performance: (performance.starts, performance.code))
        self._write(PERFORMANCES_FILE, [performance.to_dict() for performance in ordered])

    def load_holds(self):
        return {key: Hold.from_dict(key, data) for key, data in self._read(HOLDS_FILE, {}).items()}

    def save_holds(self, holds):
        self._write(HOLDS_FILE, {key: hold.to_dict() for key, hold in holds.items()})

    def new_hold_id(self, holds):
        return f"H{len(holds) + 1:04d}"

    def load_orders(self):
        return {key: Order.from_dict(key, data) for key, data in self._read(ORDERS_FILE, {}).items()}

    def save_orders(self, orders):
        self._write(ORDERS_FILE, {key: order.to_dict() for key, order in orders.items()})

    def new_order_id(self, orders):
        return f"B{len(orders) + 1:04d}"

    def load_waitlist(self):
        """Performance code to the queue of people waiting for it, first come first."""
        return self._read(WAITLIST_FILE, {})

    def save_waitlist(self, waiting):
        self._write(WAITLIST_FILE, {code: queue for code, queue in waiting.items() if queue})

    def _read(self, name, empty):
        path = self.root / name
        if not path.is_file():
            return empty
        return json.loads(path.read_text(encoding="utf-8"))

    def _write(self, name, data):
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / name
        partial = path.with_name(path.name + ".tmp")
        partial.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        partial.replace(path)
