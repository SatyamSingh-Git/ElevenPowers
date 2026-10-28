"""A starter course file for `gradebook init-course`, to be edited before `gradebook new`."""
import json
from pathlib import Path

from ..errors import ConfigError
from .course_config import course_from_dict


def starter_course(code, title, homework=8, quizzes=4, exams=2, term_days=90):
    """A weighted course with homework, quizzes and exams spread evenly over the term."""
    assignments = []
    for category, count, points in (("homework", homework, 10), ("quizzes", quizzes, 20),
                                     ("exams", exams, 100)):
        prefix = {"homework": "hw", "quizzes": "q", "exams": "exam"}[category]
        for number in range(1, count + 1):
            assignments.append({
                "id": f"{prefix}{number}",
                "title": f"{category.capitalize()} {number}",
                "category": category,
                "max_points": points,
                "due_day": max(1, term_days * number // count),
            })
    return {
        "code": code,
        "title": title,
        "policy": "weighted",
        "categories": [
            {"name": "homework", "weight": 30, "drop_lowest": 1 if homework > 2 else 0},
            {"name": "quizzes", "weight": 30},
            {"name": "exams", "weight": 40},
        ],
        "assignments": assignments,
    }


def write_starter_course(path, code, title):
    path = Path(path)
    if path.exists():
        raise ConfigError(f"{path} already exists")
    raw = starter_course(code, title)
    course_from_dict(raw)
    path.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    return path
