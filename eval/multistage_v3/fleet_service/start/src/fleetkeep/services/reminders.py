"""Reminder lines for the workshop, one per service that needs booking."""
from dataclasses import dataclass

from .scheduling import due_items

# Services with no template here are fine as they are and get no reminder.
TEMPLATES = {
    "overdue": "{vehicle}: {service} ({code}) is overdue{detail}",
    "due-soon": "{vehicle}: {service} ({code}) is due soon{detail}",
}


@dataclass(frozen=True)
class Reminder:
    vehicle_id: str
    code: str
    text: str


def _detail(item):
    parts = []
    if item.remaining_miles is not None:
        if item.remaining_miles < 0:
            parts.append(f"{-item.remaining_miles} miles over")
        else:
            parts.append(f"{item.remaining_miles} miles left")
    if item.due_date is not None:
        parts.append(f"due {item.due_date.isoformat()}")
    return f": {', '.join(parts)}" if parts else ""


def reminders(fleet, as_of):
    found = []
    for item in due_items(fleet, as_of):
        template = TEMPLATES.get(item.status)
        if template is None:
            continue
        text = template.format(vehicle=item.vehicle_id, service=item.service, code=item.code,
                               detail=_detail(item))
        found.append(Reminder(item.vehicle_id, item.code, text))
    return found
