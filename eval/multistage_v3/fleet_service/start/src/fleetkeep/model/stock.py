"""Parts the workshop keeps on its shelves.

Stock is valued at average cost: receiving parts at a new price blends it with
what is already on hand, and issuing parts leaves the unit cost as it was.
"""
from dataclasses import dataclass

from ..errors import FleetError
from .money import divide


@dataclass
class StockItem:
    number: str
    description: str
    on_hand: int = 0
    unit_cost: int = 0

    @property
    def value(self):
        return self.on_hand * self.unit_cost

    def receive(self, quantity, unit_cost):
        if quantity <= 0:
            raise FleetError("E143", text=str(quantity))
        total = self.value + unit_cost * quantity
        self.on_hand += quantity
        self.unit_cost = divide(total, self.on_hand)

    def count(self, on_hand):
        """Set the quantity on hand to what a stock count found."""
        if on_hand < 0:
            raise FleetError("E143", text=str(on_hand))
        self.on_hand = on_hand

    def issue(self, quantity):
        if quantity > self.on_hand:
            raise FleetError("E131", number=self.number, on_hand=self.on_hand)
        self.on_hand -= quantity
