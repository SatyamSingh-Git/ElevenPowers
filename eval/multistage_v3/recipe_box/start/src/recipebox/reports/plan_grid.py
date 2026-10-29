"""The week as a grid: one row per meal, one column per day."""
from ..core.plan import DAYS, MEALS

CELL = 14


def _cell(text):
    return text if len(text) <= CELL else text[:CELL - 1] + "…"


def render_grid(plan):
    meals = [meal for meal in MEALS if any(entry.meal == meal for entry in plan.entries)]
    if not meals:
        return "No meals planned.\n"
    header = " " * 10 + "".join(f"{day[:3].capitalize():<{CELL + 1}}" for day in DAYS)
    rows = [header.rstrip()]
    for meal in meals:
        cells = []
        for day in DAYS:
            titles = [entry.recipe.title for entry in plan.on(day) if entry.meal == meal]
            cells.append(f"{_cell(' + '.join(titles)) if titles else '-':<{CELL + 1}}")
        rows.append((f"{meal:<10}" + "".join(cells)).rstrip())
    return "\n".join(rows) + "\n"
