"""Course files: the JSON a teacher writes to describe a course.

Options left out of a course file take the values in DEFAULTS and
LATE_DEFAULTS. Every name a course file gives for a policy, scale or late rule
is checked against its registry when the file is loaded, not when grading.
"""
import json
from pathlib import Path

from ..errors import ConfigError
from ..grading.late import get_late_rule
from ..grading.policies import get_policy
from ..grading.scales import get_scale
from ..model.course import Assignment, Category, Course, LateSettings

DEFAULTS = {
    "term": "",
    "credits": 1.0,
    "policy": "weighted",
    "scale": "standard",
    "late_rule": "none",
    "grade_decimals": 1,
}
LATE_DEFAULTS = {"per_day": 10, "cap": 50}
REQUIRED = ("code", "title", "categories", "assignments")
WEIGHT_TOTAL = 100
MAX_DROP_LOWEST = 3
MAX_GRADE_DECIMALS = 3


def load_course(path):
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConfigError(f"{path.name}: not valid JSON ({error.msg} at line {error.lineno})") from None
    return course_from_dict(raw)


def course_from_dict(raw):
    for field in REQUIRED:
        if field not in raw:
            raise ConfigError(f"course file is missing {field}")
    settings = {key: raw.get(key, default) for key, default in DEFAULTS.items()}
    get_policy(settings["policy"])
    get_scale(settings["scale"])
    get_late_rule(settings["late_rule"])
    decimals = settings["grade_decimals"]
    if not isinstance(decimals, int) or not 0 <= decimals <= MAX_GRADE_DECIMALS:
        raise ConfigError(f"grade_decimals must be between 0 and {MAX_GRADE_DECIMALS}")
    categories = tuple(_category(entry) for entry in raw["categories"])
    _check_categories(categories, settings["policy"])
    assignments = tuple(_assignment(entry, categories) for entry in raw["assignments"])
    _check_assignments(assignments)
    return Course(
        code=str(raw["code"]),
        title=str(raw["title"]),
        term=str(settings["term"]),
        credits=float(settings["credits"]),
        policy=settings["policy"],
        scale=settings["scale"],
        late_rule=settings["late_rule"],
        late=_late_settings(raw.get("late", {})),
        grade_decimals=decimals,
        categories=categories,
        assignments=assignments,
    )


def course_to_dict(course):
    return {
        "code": course.code,
        "title": course.title,
        "term": course.term,
        "credits": course.credits,
        "policy": course.policy,
        "scale": course.scale,
        "late_rule": course.late_rule,
        "late": dict(vars(course.late)),
        "grade_decimals": course.grade_decimals,
        "categories": [
            {"name": c.name, "weight": c.weight, "drop_lowest": c.drop_lowest}
            for c in course.categories
        ],
        "assignments": [
            {"id": a.assignment_id, "title": a.title, "category": a.category,
             "max_points": a.max_points, "due_day": a.due_day}
            for a in course.assignments
        ],
    }


def _late_settings(raw):
    for key in raw:
        if key not in LATE_DEFAULTS:
            raise ConfigError(f"unknown late setting {key}")
    values = {**LATE_DEFAULTS, **raw}
    for key, value in values.items():
        if not isinstance(value, (int, float)) or value < 0:
            raise ConfigError(f"late.{key} must be a number of at least 0")
    return LateSettings(**values)


def _category(entry):
    name = str(entry["name"])
    drop = entry.get("drop_lowest", 0)
    if not isinstance(drop, int) or not 0 <= drop <= MAX_DROP_LOWEST:
        raise ConfigError(f"{name}: drop_lowest must be between 0 and {MAX_DROP_LOWEST}")
    return Category(name=name, weight=float(entry.get("weight", 0)), drop_lowest=drop)


def _check_categories(categories, policy):
    names = [category.name for category in categories]
    for name in names:
        if names.count(name) > 1:
            raise ConfigError(f"duplicate category {name}")
    if policy == "weighted":
        total = sum(category.weight for category in categories)
        if total != WEIGHT_TOTAL:
            raise ConfigError(f"category weights add up to {total:g}, not {WEIGHT_TOTAL}")


def _assignment(entry, categories):
    assignment_id = str(entry["id"])
    category = str(entry["category"])
    if category not in {c.name for c in categories}:
        raise ConfigError(f"assignment {assignment_id} names unknown category {category}")
    max_points = float(entry["max_points"])
    if max_points <= 0:
        raise ConfigError(f"{assignment_id}: max_points must be positive")
    due_day = entry["due_day"]
    if not isinstance(due_day, int) or due_day < 1:
        raise ConfigError(f"{assignment_id}: due_day must be a term day from 1")
    return Assignment(assignment_id, str(entry.get("title", assignment_id)), category, max_points, due_day)


def _check_assignments(assignments):
    seen = set()
    for assignment in assignments:
        if assignment.assignment_id in seen:
            raise ConfigError(f"duplicate assignment {assignment.assignment_id}")
        seen.add(assignment.assignment_id)
