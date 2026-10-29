"""Shop time and availability for each vehicle over a period."""
from ..services.downtime import availability, days_down, orders_in


def downtime_rows(fleet, period):
    return [(vehicle.id, len(orders_in(fleet, vehicle.id, period)),
             days_down(fleet, vehicle.id, period),
             days_down(fleet, vehicle.id, period, breakdowns_only=True),
             availability(fleet, vehicle.id, period))
            for vehicle in fleet.vehicles()]
