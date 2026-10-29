from datetime import date

import pytest

from recipebox.core.plan import MealEntry, Plan
from recipebox.errors import PlanError
from recipebox.reports.prep_report import render_prep
from recipebox.services.prep import prep_list, task_verb
from recipebox.storage.plan_calendar import parse_week, plan_to_ics


def test_task_verb():
    assert task_verb("finely chopped") == "chop"
    assert task_verb("melted, cooled") == "melt"
    assert task_verb("to taste") is None


def test_prep_list_adds_up_across_meals(soup, pancakes):
    plan = Plan([MealEntry("monday", "lunch", soup), MealEntry("tuesday", "lunch", soup, servings=4),
                 MealEntry("tuesday", "breakfast", pancakes)])
    tasks = prep_list(plan)
    assert [(task.verb, task.name) for task in tasks] == [("chop", "tomato"), ("melt", "butter")]
    assert tasks[0].totals == [("", 18)]
    assert render_prep(tasks) == (
        "chop  tomato  18    for Tomato Soup\n"
        "melt  butter  30 g  for Fluffy Pancakes\n"
    )


def test_parse_week():
    assert parse_week("2026-11-02") == date(2026, 11, 2)
    with pytest.raises(PlanError, match="--week-of must be a Monday, 2026-11-04 is a wednesday"):
        parse_week("2026-11-04")
    with pytest.raises(PlanError, match="cannot read date soon"):
        parse_week("soon")


def test_calendar(pancakes):
    ics = plan_to_ics(Plan([MealEntry("wednesday", "breakfast", pancakes)]), date(2026, 11, 2))
    lines = ics.split("\r\n")
    assert lines[:3] == ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//recipebox//meal plan//EN"]
    assert "DTSTART:20261104T080000" in lines
    assert "DTEND:20261104T084500" in lines
    assert "SUMMARY:Breakfast: Fluffy Pancakes" in lines
    assert ics.endswith("END:VCALENDAR\r\n")
