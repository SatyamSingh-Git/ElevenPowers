"""Reports over a period of days, by the name the command line and the layouts use."""
from .costs import cost_rows
from .downtime import downtime_rows
from .fuel import fuel_rows
from .spend import spend_rows

PERIOD_REPORTS = {
    "costs": cost_rows,
    "fuel": fuel_rows,
    "spend": spend_rows,
    "downtime": downtime_rows,
}
