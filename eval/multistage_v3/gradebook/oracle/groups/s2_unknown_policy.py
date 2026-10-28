"""Stage 2: an unknown policy names the current choices."""
import json

import pytest

from gradebook.storage.course_config import load_course

COURSE = {
    "code": "ART",
    "title": "Studio Art",
    "categories": [{"name": "projects", "weight": 100}],
    "assignments": [{"id": "pr1", "category": "projects", "max_points": 10, "due_day": 3}],
}


def test_unknown_policy_message(tmp_path):
    path = tmp_path / "course.json"
    path.write_text(json.dumps(dict(COURSE, policy="average")), encoding="utf-8")
    with pytest.raises(Exception) as error:
        load_course(path)
    assert str(error.value) == "unknown scoring policy average; choose weighted or total_points"


def test_old_name_still_loads(tmp_path):
    path = tmp_path / "course.json"
    path.write_text(json.dumps(dict(COURSE, policy="points")), encoding="utf-8")
    load_course(path)
