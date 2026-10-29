"""The parts shelf: what is on hand and what it is worth at average cost."""
from ..model.money import dollars


def stock_rows(fleet):
    return [(item.number, item.description, item.on_hand, dollars(item.unit_cost),
             dollars(item.value))
            for item in fleet.stock()]
