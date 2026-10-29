"""Savings goals: a target amount in an account by a date."""
from dataclasses import dataclass

from ..errors import NotFound, ValidationError
from ..model.dates import Month
from ..model.records import Goal
from ..storage import files
from .accounts import balances, require_account


@dataclass(frozen=True)
class Progress:
    goal: Goal
    saved: int
    months_left: int

    @property
    def still_needed(self):
        return max(self.goal.target - self.saved, 0)

    @property
    def per_month(self):
        """What to put aside each remaining month, rounded up to the cent."""
        if self.months_left <= 0:
            return self.still_needed
        return -(-self.still_needed // self.months_left)


def add_goal(workspace, goal):
    goals = files.load_goals(workspace)
    if any(existing.name == goal.name for existing in goals):
        raise ValidationError(f"goal already exists: {goal.name}")
    require_account(workspace, goal.account)
    if goal.target <= 0:
        raise ValidationError("a goal's target must be more than zero")
    goals.append(goal)
    files.save_goals(workspace, goals)
    return goal


def remove_goal(workspace, name):
    goals = files.load_goals(workspace)
    keep = [goal for goal in goals if goal.name != name]
    if len(keep) == len(goals):
        raise NotFound(f"no goal called {name}")
    files.save_goals(workspace, keep)


def progress(workspace, today):
    """Each goal's progress as of `today`; today's month and the goal's month both count."""
    balance = balances(workspace, through=today)
    now = Month.of(today)
    result = []
    for goal in files.load_goals(workspace):
        due = Month.of(goal.by)
        months_left = (due.year - now.year) * 12 + due.month - now.month + 1
        result.append(Progress(goal, balance.get(goal.account, 0), max(months_left, 0)))
    return result
