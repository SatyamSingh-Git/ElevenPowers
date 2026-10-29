"""The week's plan as `recipebox plan show` prints it."""


def render_plan(plan, energy=None):
    """One block per planned day; `energy` ({day: kcal}) adds a line per day."""
    if not len(plan):
        return "No meals planned.\n"
    out = []
    for day in plan.days():
        if out:
            out.append("")
        out.append(day.capitalize())
        for entry in plan.on(day):
            out.append(f"  {entry.meal:<10} {entry.recipe.title} (serves {entry.portions})")
        if energy is not None:
            out.append(f"  {'energy':<10} {energy[day]} kcal per person")
    return "\n".join(out) + "\n"
