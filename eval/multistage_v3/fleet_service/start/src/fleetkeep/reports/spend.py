"""Fleet spending by calendar month.

Each month of the period gets a row, even a month with no spending. Fuel is
counted in the month it was bought and a work order in the month it closed, at
its parts plus its labour.
"""
from ..model.money import dollars


def _month(day):
    return f"{day.year:04d}-{day.month:02d}"


def spend_rows(fleet, period):
    months = {}
    for day in period.each_day():
        months.setdefault(_month(day), [0, 0, 0])
    for entry in fleet.fuel():
        if entry.day in period:
            months[_month(entry.day)][0] += entry.cost
    for order in fleet.orders():
        if order.closed is not None and order.closed in period:
            spent = months[_month(order.closed)]
            spent[1] += order.parts_total + order.labour_total
            spent[2] += 1
    return [(month, dollars(fuel), orders, dollars(maintenance), dollars(fuel + maintenance))
            for month, (fuel, maintenance, orders) in months.items()]
