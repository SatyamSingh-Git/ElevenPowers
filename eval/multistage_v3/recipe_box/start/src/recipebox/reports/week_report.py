"""The table `recipebox plan nutrition` prints: one row per planned day and an average."""

# (summary field, column heading, decimals)
TABLE = (
    ("kcal", "kcal", 0),
    ("protein_g", "protein", 1),
    ("fat_g", "fat", 1),
    ("carbs_g", "carbs", 1),
)

WIDTH = 9


def _row(label, amounts):
    cells = [f"{amounts.get(name, 0.0):>{WIDTH}.{places}f}" for name, _, places in TABLE]
    return f"{label:<10}" + "".join(cells)


def render_week(week, average):
    if not week:
        return "No meals planned.\n"
    header = f"{'day':<10}" + "".join(f"{heading:>{WIDTH}}" for _, heading, _ in TABLE)
    out = [header]
    out += [_row(day.day, day.amounts) for day in week]
    out.append(_row("average", average))
    return "\n".join(out) + "\n"
