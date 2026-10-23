import pytest

from warden.conditions import Condition
from warden.errors import ConditionError


def holds(text, user=None, resource=None):
    return Condition(text).evaluate(user or {}, resource or {})


def test_equality_between_attributes():
    assert holds("user.dept == resource.dept", {"dept": "ops"}, {"dept": "ops"})
    assert not holds("user.dept == resource.dept", {"dept": "ops"}, {"dept": "hr"})


def test_literals():
    assert holds('user.team == "data platform"', {"team": "data platform"})
    assert holds("resource.public == true", resource={"public": True})
    assert holds("user.level == 3", {"level": 3})


def test_missing_attribute_never_holds():
    assert not holds("user.dept == resource.dept", {}, {"dept": "ops"})
    assert not holds("user.dept != resource.dept", {}, {"dept": "ops"})


def test_and_needs_every_clause():
    text = 'user.dept == resource.dept and resource.stage != "draft"'
    assert holds(text, {"dept": "ops"}, {"dept": "ops", "stage": "final"})
    assert not holds(text, {"dept": "ops"}, {"dept": "ops", "stage": "draft"})


def test_failing_lists_unmet_clauses():
    condition = Condition('user.dept == resource.dept and resource.stage != "draft"')
    assert condition.failing({"dept": "ops"}, {"dept": "hr", "stage": "draft"}) == [
        "user.dept == resource.dept", 'resource.stage != "draft"']


@pytest.mark.parametrize("text, message", [
    ("user.dept ==", "bad condition"),
    ("user.dept = 3", "bad condition"),
    ("host.name == 3", "unknown attribute namespace: host"),
    ("dept == 3", "bad operand: dept"),
])
def test_bad_conditions(text, message):
    with pytest.raises(ConditionError, match=message):
        Condition(text)
