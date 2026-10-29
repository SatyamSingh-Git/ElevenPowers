"""A week's nutrition: what one person eats each planned day, and the daily average."""
from dataclasses import dataclass

from .nutrition import totals


@dataclass
class DayIntake:
    day: str
    # Summary field -> amount for one person, unrounded.
    amounts: dict
    meals: int


def week_intake(plan):
    """One DayIntake per planned day, Monday first. Each meal counts one serving of its recipe."""
    week = []
    for day in plan.days():
        amounts = {}
        entries = plan.on(day)
        for entry in entries:
            sums, _ = totals(entry.recipe)
            for name, value in sums.items():
                amounts[name] = amounts.get(name, 0.0) + value / entry.recipe.servings
        week.append(DayIntake(day, amounts, len(entries)))
    return week


def daily_average(week):
    """Field -> average over the planned days; empty when nothing is planned."""
    if not week:
        return {}
    names = week[0].amounts.keys()
    return {name: sum(day.amounts.get(name, 0.0) for day in week) / len(week) for name in names}
