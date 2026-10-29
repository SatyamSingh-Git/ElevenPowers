"""Column names and alignment for each report, in the order its rows hold them."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    name: str
    align: str = "left"


def _right(*names):
    return tuple(Column(name, "right") for name in names)


LAYOUTS = {
    "vehicles": (Column("id"), Column("class"), Column("make"), Column("model"),
                 *_right("year", "odometer"), Column("last_reading"), *_right("miles_per_day"),
                 Column("retired")),
    "due": (Column("vehicle"), Column("code"), Column("service"),
            *_right("due_miles", "remaining_miles"), Column("due_date"),
            *_right("remaining_days"), Column("status")),
    "costs": (Column("vehicle"),
              *_right("miles", "fuel", "maintenance", "total", "cost_per_mile")),
    "fuel": (Column("vehicle"), *_right("fills", "gallons", "fuel_cost", "miles", "mpg")),
    "downtime": (Column("vehicle"), *_right("orders", "days_down", "breakdown_days", "availability")),
    "orders": (Column("id"), Column("vehicle"), Column("status"), Column("opened"),
               Column("closed"), Column("services")),
    "history": (Column("date"), Column("code"), Column("service"), *_right("odometer"),
                Column("order")),
    "defects": (Column("id"), Column("vehicle"), Column("reported"), Column("severity"),
                Column("description"), Column("order"), Column("fixed")),
    "spend": (Column("month"), *_right("fuel", "orders", "maintenance", "total")),
    "stock": (Column("number"), Column("description"), *_right("on_hand", "unit_cost", "value")),
    "catalog": (Column("code"), Column("service"), *_right("miles", "months"), Column("classes")),
    "summary": (Column("vehicle"),
                *_right("miles", "total", "cost_per_mile", "mpg", "days_down", "availability")),
}
