"""The prep list as `recipebox plan prep` prints it."""
from ..core.quantity import Quantity, display_quantity


def _amounts(task):
    return " + ".join(display_quantity(Quantity(amount, unit)) for unit, amount in task.totals)


def render_prep(tasks):
    if not tasks:
        return "Nothing to prepare.\n"
    verb_width = max(len(task.verb) for task in tasks) + 2
    name_width = max(len(task.name) for task in tasks) + 2
    amount_width = max(len(_amounts(task)) for task in tasks) + 2
    lines = []
    for task in tasks:
        line = f"{task.verb.ljust(verb_width)}{task.name.ljust(name_width)}{_amounts(task).ljust(amount_width)}"
        lines.append(f"{line}for {', '.join(task.recipes)}\n")
    return "".join(lines)
