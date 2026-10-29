"""The pantry as `recipebox pantry list` prints it."""
from ..core.quantity import display_quantity

STAPLE = "staple"


def render_pantry(pantry):
    items = pantry.items()
    if not items:
        return "The pantry is empty.\n"
    width = max(len(item.name) for item in items) + 2
    lines = []
    for item in items:
        held = STAPLE if item.staple else display_quantity(item.quantity)
        lines.append(f"{item.name.ljust(width)}{held}\n")
    return "".join(lines)
