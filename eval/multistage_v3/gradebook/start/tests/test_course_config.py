import json

import pytest

from gradebook.errors import ConfigError
from gradebook.storage.course_config import course_from_dict, course_to_dict, load_course


def test_defaults_fill_in_missing_options(course_data):
    for option in ("late_rule", "grade_decimals", "late"):
        del course_data[option]
    course = course_from_dict(course_data)
    assert course.policy == "weighted"
    assert course.scale == "standard"
    assert course.late_rule == "none"
    assert course.grade_decimals == 1
    assert course.late.per_day == 10
    assert course.late.cap == 50


def test_load_course_reads_json(tmp_path, course_data):
    path = tmp_path / "course.json"
    path.write_text(json.dumps(course_data), encoding="utf-8")
    assert load_course(path).code == "ALG1"


def test_round_trip_through_dict(course):
    assert course_from_dict(course_to_dict(course)) == course


def test_weights_must_add_up(course_data):
    course_data["categories"][0]["weight"] = 50
    with pytest.raises(ConfigError, match="category weights add up to 110, not 100"):
        course_from_dict(course_data)


def test_points_policy_ignores_weights(course_data):
    course_data["policy"] = "points"
    for category in course_data["categories"]:
        category["weight"] = 0
    assert course_from_dict(course_data).policy == "points"


def test_unknown_policy(course_data):
    course_data["policy"] = "average"
    with pytest.raises(ConfigError) as error:
        course_from_dict(course_data)
    assert str(error.value) == "unknown scoring policy average; choose weighted or points"


def test_unknown_scale_and_late_rule(course_data):
    course_data["scale"] = "stars"
    with pytest.raises(ConfigError, match="unknown letter scale stars"):
        course_from_dict(course_data)
    course_data["scale"] = "standard"
    course_data["late_rule"] = "harsh"
    with pytest.raises(ConfigError, match="unknown late rule harsh"):
        course_from_dict(course_data)


def test_assignment_needs_a_known_category(course_data):
    course_data["assignments"][0]["category"] = "labs"
    with pytest.raises(ConfigError, match="assignment hw1 names unknown category labs"):
        course_from_dict(course_data)


def test_drop_lowest_limit(course_data):
    course_data["categories"][0]["drop_lowest"] = 4
    with pytest.raises(ConfigError, match="drop_lowest must be between 0 and 3"):
        course_from_dict(course_data)


def test_unknown_late_setting(course_data):
    course_data["late"]["grace"] = 2
    with pytest.raises(ConfigError, match="unknown late setting grace"):
        course_from_dict(course_data)


def test_duplicate_assignment(course_data):
    course_data["assignments"].append(dict(course_data["assignments"][0]))
    with pytest.raises(ConfigError, match="duplicate assignment hw1"):
        course_from_dict(course_data)
