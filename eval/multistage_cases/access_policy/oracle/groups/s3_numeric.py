from warden import Evaluator, Request, User, parse_policy

POLICY = """\
role staff
allow staff read payroll/** when user.clearance >= 3
allow staff write grades/* when user.level < resource.level
"""


def allowed(user_attrs, action="read", resource="payroll/may", resource_attrs=None):
    request = Request(User("alice", ("staff",), user_attrs), action, resource, resource_attrs or {})
    return Evaluator(parse_policy(POLICY)).decide(request).allowed


def test_clearance_compares_as_a_number():
    assert allowed({"clearance": 10}) is True
    assert allowed({"clearance": 4}) is True
    assert allowed({"clearance": 3}) is True
    assert allowed({"clearance": 2}) is False


def test_numeric_strings_compare_as_numbers():
    assert allowed({"clearance": "10"}) is True
    assert allowed({"clearance": "2"}) is False


def test_attribute_against_attribute():
    assert allowed({"level": 9}, "write", "grades/x", {"level": 10}) is True
    assert allowed({"level": "9"}, "write", "grades/x", {"level": "10"}) is True
    assert allowed({"level": 11}, "write", "grades/x", {"level": 10}) is False
