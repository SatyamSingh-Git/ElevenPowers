"""The fleet: every record in one place, and the rules for adding to it.

Importers and reports work through a `Fleet`; the application services in this
package build on it for the command line.
"""
from collections import defaultdict
from dataclasses import replace

from ..config import Settings
from ..errors import FleetError
from ..model.catalog import service_spec
from ..model.workorder import ServiceRecord


class Fleet:
    def __init__(self, settings=None):
        self.settings = settings or Settings()
        self._vehicles = {}
        self._readings = defaultdict(list)
        self._fuel = defaultdict(list)
        self._orders = {}
        self._history = defaultdict(list)
        self._stock = {}
        self._cards = {}
        self._defects = {}
        self._treads = []

    @classmethod
    def restore(cls, settings, vehicles, readings, fuel, orders, history, stock, cards,
                defects, treads):
        """A fleet rebuilt from saved records, which were checked when they were added."""
        fleet = cls(settings)
        fleet._vehicles = {vehicle.id: vehicle for vehicle in vehicles}
        for reading in sorted(readings, key=lambda r: (r.day, r.odometer)):
            fleet._readings[reading.vehicle_id].append(reading)
        for entry in fuel:
            fleet._fuel[entry.vehicle_id].append(entry)
        fleet._orders = {order.id: order for order in orders}
        for record in history:
            fleet._history[record.vehicle_id].append(record)
        fleet._stock = {item.number: item for item in stock}
        fleet._cards = dict(cards)
        fleet._defects = {defect.id: defect for defect in defects}
        fleet._treads = list(treads)
        return fleet

    # Vehicles

    def add_vehicle(self, vehicle):
        if vehicle.id in self._vehicles:
            raise FleetError("E104", vehicle=vehicle.id)
        self._vehicles[vehicle.id] = vehicle

    def vehicle(self, vehicle_id):
        try:
            return self._vehicles[vehicle_id]
        except KeyError:
            raise FleetError("E103", vehicle=vehicle_id) from None

    def vehicles(self):
        return [self._vehicles[key] for key in sorted(self._vehicles)]

    def active_vehicles(self, day):
        """Vehicles in service on `day`: already delivered and not yet retired."""
        return [vehicle for vehicle in self.vehicles() if vehicle.in_service_on(day)]

    def retire_vehicle(self, vehicle_id, day):
        vehicle = self.vehicle(vehicle_id)
        if day < vehicle.in_service:
            raise FleetError("E109", vehicle=vehicle.id, in_service=vehicle.in_service.isoformat())
        self._vehicles[vehicle.id] = replace(vehicle, retired=day)
        return self._vehicles[vehicle.id]

    # Odometer readings

    def add_reading(self, reading):
        vehicle = self.vehicle(reading.vehicle_id)
        readings = self._readings[vehicle.id]
        if readings:
            latest = readings[-1]
            if reading.day < latest.day:
                raise FleetError("E107", vehicle=vehicle.id, day=reading.day.isoformat(),
                                 latest=latest.day.isoformat())
            previous, since = latest.odometer, latest.day
        else:
            previous, since = vehicle.start_odometer, vehicle.in_service
        if reading.odometer < previous:
            raise FleetError("E105", vehicle=vehicle.id, value=reading.odometer, previous=previous)
        days = max((reading.day - since).days, 1)
        miles = reading.odometer - previous
        if miles > self.settings.max_daily_miles * days:
            raise FleetError("E106", vehicle=vehicle.id, miles=miles, days=days)
        readings.append(reading)

    def correct_reading(self, vehicle_id, day, odometer):
        """Replace a mistyped reading; it must still sit between its neighbours."""
        readings = self._readings[self.vehicle(vehicle_id).id]
        index = next((i for i, r in enumerate(readings) if r.day == day), None)
        if index is None:
            raise FleetError("E146", vehicle=vehicle_id, day=day.isoformat())
        before = readings[index - 1].odometer if index else self.vehicle(vehicle_id).start_odometer
        if odometer < before:
            raise FleetError("E105", vehicle=vehicle_id, value=odometer, previous=before)
        if index + 1 < len(readings) and odometer > readings[index + 1].odometer:
            raise FleetError("E105", vehicle=vehicle_id, value=readings[index + 1].odometer,
                             previous=odometer)
        readings[index] = replace(readings[index], odometer=odometer)
        return readings[index]

    def readings(self, vehicle_id=None):
        if vehicle_id is not None:
            return list(self._readings[vehicle_id])
        return [r for key in sorted(self._readings) for r in self._readings[key]]

    def odometer_on(self, vehicle_id, day):
        """The latest odometer reading on or before `day`; the start odometer before any."""
        value = self.vehicle(vehicle_id).start_odometer
        for reading in self._readings[vehicle_id]:
            if reading.day > day:
                break
            value = reading.odometer
        return value

    # Fuel

    def add_fuel(self, entry):
        self.vehicle(entry.vehicle_id)
        self._fuel[entry.vehicle_id].append(entry)

    def fuel(self, vehicle_id=None):
        if vehicle_id is not None:
            return list(self._fuel[vehicle_id])
        return [e for key in sorted(self._fuel) for e in self._fuel[key]]

    def assign_card(self, card, vehicle_id):
        self._cards[card] = self.vehicle(vehicle_id).id

    def card_vehicle(self, card):
        try:
            return self._cards[card]
        except KeyError:
            raise FleetError("E113", card=card) from None

    def cards(self):
        return sorted(self._cards.items())

    # Work orders

    def add_order(self, order):
        self.vehicle(order.vehicle_id)
        self._orders[order.id] = order

    def order(self, order_id):
        try:
            return self._orders[order_id]
        except KeyError:
            raise FleetError("E121", order=order_id) from None

    def remove_order(self, order_id):
        del self._orders[self.order(order_id).id]

    def orders(self, vehicle_id=None):
        orders = [self._orders[key] for key in sorted(self._orders)]
        if vehicle_id is None:
            return orders
        return [order for order in orders if order.vehicle_id == vehicle_id]

    # Service history

    def record_service(self, vehicle_id, code, day, odometer, order_id=""):
        vehicle = self.vehicle(vehicle_id)
        spec = service_spec(code)
        if not spec.applies_to(vehicle.vehicle_class):
            raise FleetError("E124", code=code, vehicle_class=vehicle.vehicle_class)
        record = ServiceRecord(vehicle.id, spec.code, day, odometer, order_id)
        self._history[vehicle.id].append(record)
        return record

    def history(self, vehicle_id=None):
        if vehicle_id is not None:
            records = self._history[vehicle_id]
        else:
            records = [r for key in sorted(self._history) for r in self._history[key]]
        return sorted(records, key=lambda r: (r.vehicle_id, r.day, r.odometer, r.code))

    def last_service(self, vehicle_id, code):
        done = [r for r in self._history[vehicle_id] if r.code == code]
        return max(done, key=lambda r: (r.day, r.odometer), default=None)

    # Parts stock

    def stock_item(self, number):
        """The stocked part with this number, or None for a part bought in for one job."""
        return self._stock.get(number)

    def add_stock_item(self, item):
        self._stock[item.number] = item

    def stock(self):
        return [self._stock[key] for key in sorted(self._stock)]

    # Inspections

    def add_defect(self, defect):
        self.vehicle(defect.vehicle_id)
        self._defects[defect.id] = defect

    def defect(self, defect_id):
        try:
            return self._defects[defect_id]
        except KeyError:
            raise FleetError("E161", defect=defect_id) from None

    def defects(self, vehicle_id=None):
        defects = [self._defects[key] for key in sorted(self._defects)]
        return [d for d in defects if vehicle_id is None or d.vehicle_id == vehicle_id]

    def add_tread(self, reading):
        self.vehicle(reading.vehicle_id)
        self._treads.append(reading)

    def treads(self, vehicle_id=None):
        readings = sorted(self._treads, key=lambda r: (r.vehicle_id, r.day, r.position))
        return [r for r in readings if vehicle_id is None or r.vehicle_id == vehicle_id]
